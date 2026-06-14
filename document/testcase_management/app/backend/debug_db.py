import sys
import os

back = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, back)

from database import SessionLocal
from models import Report, TestPlanTestCase
import json

db = SessionLocal()

try:
    report_id = 113

    report = db.query(Report).filter(Report.id == report_id).first()
    if report:
        print(f"Report: {report.id}, status={report.status}")

        if report.snapshot_data and report.status == 'APPROVED':
            try:
                snapshot = json.loads(report.snapshot_data)
                snapshot_case_count = len(snapshot.get('test_cases', []))

                plan_case_count = db.query(TestPlanTestCase).filter(
                    TestPlanTestCase.test_plan_id == report.test_plan_id
                ).count()

                print(f"\nsnapshot_case_count: {snapshot_case_count}")
                print(f"plan_case_count: {plan_case_count}")

                if snapshot_case_count > 0:
                    test_cases = snapshot.get('test_cases', [])
                    print(f"\n使用快照数据!")
                    print(f"test_cases 返回数量: {len(test_cases)}")

                    # 看第一条
                    if test_cases:
                        print(f"第一条: {test_cases[0]}")
                else:
                    print("\n不使用快照")

            except Exception as e:
                print(f"Error: {e}")
finally:
    db.close()