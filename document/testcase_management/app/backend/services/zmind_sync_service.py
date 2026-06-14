import logging
import requests
import time
import concurrent.futures
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from config import ZMIND_API_KEY, ZMIND_API_URL
from database import engine

logger = logging.getLogger(__name__)

ZMIND_SYNC_CONCURRENCY = 3  # 并发数（降低以避免触发Zmind限流）
ZMIND_SYNC_TIMEOUT = 30  # 单个请求超时（秒）
ZMIND_SYNC_DELAY = 0.5  # 请求间隔（秒），避免触发限流
BATCH_SIZE = 50  # 每批处理数量


class ZmindSyncService:
    """Zmind PR同步服务（稳定版 - 独立连接）"""

    def __init__(self, db: Session = None):
        # 如果传入db则使用，否则创建新的
        self._external_db = db
        if db:
            self.db = db
        else:
            self.db = None

    def _get_db(self) -> Session:
        """获取数据库连接"""
        if self.db:
            return self.db
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()

    def _close_db(self, db: Session):
        """关闭数据库连接（仅关闭非外部传入的）"""
        if db and not self._external_db:
            db.close()

    def _fetch_pr_info(self, zmind_issue_id: str, headers: dict) -> dict:
        """从Zmind API获取PR信息（带重试机制）"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 添加延迟，避免触发Zmind API限流
                time.sleep(ZMIND_SYNC_DELAY)
                
                url = f"{ZMIND_API_URL}/issues/{zmind_issue_id}.json"
                response = requests.get(url, headers=headers, timeout=ZMIND_SYNC_TIMEOUT)

                if response.status_code == 200:
                    data = response.json()
                    issue = data.get('issue', {})
                    return {
                        "subject": issue.get('subject', ''),
                        "status": issue.get('status', {}).get('name', ''),
                        "severity": self._extract_severity(issue.get('custom_fields', []))
                    }
                elif response.status_code == 403 and attempt < max_retries - 1:
                    # 403可能是限流，等待后重试
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Zmind API返回403，等待{wait_time}秒后重试: {zmind_issue_id}")
                    time.sleep(wait_time)
                    continue
                else:
                    return {"error": f"HTTP {response.status_code}"}
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return {"error": str(e)}
        return {"error": "max retries exceeded"}

    def _extract_severity(self, custom_fields: list) -> str:
        """提取Severity字段值"""
        for field in custom_fields:
            if field.get('name') == 'Severity':
                return field.get('value', '')
        return ''

    def sync_all_pr_status(self):
        """同步所有项目的PR状态（每个项目独立事务）"""
        from models import Project, TestCaseZmindLink, TestCase

        if not ZMIND_API_KEY:
            logger.warning("系统未配置Zmind API Key，跳过同步")
            return {"updated": 0, "failed": 0, "message": "未配置API Key"}

        headers = {
            'X-Redmine-API-Key': ZMIND_API_KEY,
            'Content-Type': 'application/json'
        }

        db = self._get_db()
        projects = db.query(Project).all()
        total_updated = 0
        total_failed = 0

        for project in projects:
            # 每个项目使用独立连接
            project_db = self._create_db_session()
            try:
                links = project_db.query(TestCaseZmindLink).join(
                    TestCase, TestCase.id == TestCaseZmindLink.test_case_id
                ).filter(TestCase.primary_project_id == project.id).all()

                if not links:
                    continue

                logger.info(f"项目 {project.id} 开始同步 {len(links)} 个PR")

                link_data = [(link.id, link.zmind_issue_id) for link in links]

                with concurrent.futures.ThreadPoolExecutor(max_workers=ZMIND_SYNC_CONCURRENCY) as executor:
                    future_to_link = {
                        executor.submit(self._fetch_pr_info, zmind_id, headers): link_id
                        for link_id, zmind_id in link_data
                    }

                    for future in concurrent.futures.as_completed(future_to_link):
                        link_id = future_to_link[future]
                        try:
                            result = future.result()
                            link = project_db.query(TestCaseZmindLink).filter(TestCaseZmindLink.id == link_id).first()
                            if link:
                                if "error" in result:
                                    total_failed += 1
                                else:
                                    link.zmind_issue_subject = result.get('subject', link.zmind_issue_subject)
                                    link.zmind_issue_status = result.get('status', link.zmind_issue_status)
                                    if result.get('severity'):
                                        link.zmind_issue_severity = result.get('severity')
                                    total_updated += 1
                        except Exception as e:
                            total_failed += 1
                            logger.warning(f"PR同步异常: {e}")

                project_db.commit()
                logger.info(f"项目 {project.id} 同步完成: 成功={total_updated}")

            except Exception as e:
                logger.error(f"项目 {project.id} 同步失败: {e}")
                project_db.rollback()
                total_failed += 1
            finally:
                self._close_db(project_db)

        if not self._external_db:
            self._close_db(db)

        return {
            "updated": total_updated,
            "failed": total_failed,
            "message": f"同步完成，成功: {total_updated}，失败: {total_failed}"
        }

    def _create_db_session(self) -> Session:
        """创建独立的数据库连接"""
        worker_engine = create_engine(
            engine.url,
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True
        )
        SessionLocal = sessionmaker(bind=worker_engine)
        return SessionLocal()

    def sync_single_testcase_pr(self, testcase_id: int):
        """同步单个测试用例的PR状态"""
        from models import TestCaseZmindLink

        if not ZMIND_API_KEY:
            return {"updated": 0, "failed": 0, "message": "未配置API Key"}

        headers = {
            'X-Redmine-API-Key': ZMIND_API_KEY,
            'Content-Type': 'application/json'
        }

        db = self._get_db()
        links = db.query(TestCaseZmindLink).filter(
            TestCaseZmindLink.test_case_id == testcase_id
        ).all()

        if not links:
            return {"updated": 0, "failed": 0, "message": "无关联PR"}

        updated = 0
        failed = 0

        for link in links:
            result = self._fetch_pr_info(link.zmind_issue_id, headers)
            if "error" in result:
                failed += 1
            else:
                link.zmind_issue_subject = result.get('subject', link.zmind_issue_subject)
                link.zmind_issue_status = result.get('status', link.zmind_issue_status)
                if result.get('severity'):
                    link.zmind_issue_severity = result.get('severity')
                updated += 1

        db.commit()

        if not self._external_db:
            self._close_db(db)

        return {
            "updated": updated,
            "failed": failed,
            "message": f"刷新完成，成功: {updated}，失败: {failed}"
        }