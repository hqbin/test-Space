"""
异步导入任务管理服务
用例导入改为异步模式：上传后立即返回任务ID，后台线程处理，前端轮询进度
"""
import threading
import uuid
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ImportTask:
    task_id: str
    status: str = "pending"  # pending, parsing, importing, committing, done, error
    message: str = ""
    progress: int = 0
    current: int = 0
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    result: Optional[Dict[str, Any]] = None


class ImportTaskManager:
    """内存中的导入任务管理器"""

    def __init__(self):
        self._tasks: Dict[str, ImportTask] = {}
        self._lock = threading.Lock()

    def create_task(self) -> str:
        task_id = str(uuid.uuid4())[:8]
        with self._lock:
            self._tasks[task_id] = ImportTask(task_id=task_id)
        return task_id

    def get_task(self, task_id: str) -> Optional[ImportTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs):
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                for k, v in kwargs.items():
                    setattr(task, k, v)

    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """清理超过1小时的旧任务"""
        now = time.time()
        with self._lock:
            expired = [
                tid for tid, t in self._tasks.items()
                if now - t.created_at > max_age_seconds
            ]
            for tid in expired:
                del self._tasks[tid]


# 全局单例
import_task_manager = ImportTaskManager()
