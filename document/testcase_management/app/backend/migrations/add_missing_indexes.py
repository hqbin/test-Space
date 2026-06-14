"""
数据库迁移脚本 - 为高频查询外键字段补全缺失索引

背景：
    以下表的外键字段在 models.py 中未设置 index=True，
    随数据量增长，JOIN 和 WHERE 查询会退化为全表扫描。
    本脚本为这些字段补全索引，提升查询性能。

涉及表：
    - test_executions          (test_plan_id, test_case_id, executor_id)
    - reports                  (test_plan_id)
    - test_case_zmind_links    (test_case_id, test_plan_id)
    - testcase_history         (testcase_id)
    - user_roles               (user_id, role_id)
    - user_projects            (user_id, project_id)
    - user_teams               (user_id, team_id)
    - team_projects            (team_id, project_id)
    - test_plans               (project_id, reviewer_id)
    - teams                    (department_id, leader_id)
    - department_managers      (department_id, user_id)
    - user_departments         (user_id, department_id)
    - version_notify_group_members (group_id, user_id)
    - notification_recipients  (notification_id)
    - zmind_sync_status        (project_id)

脚本设计为幂等（可重复执行），通过 inspector 先检查索引是否存在。

创建日期: 2026-06-03
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from database import engine
from sqlalchemy import text, inspect


# 每一项: (index_name, table_name, column_name)
INDEXES_TO_CREATE = [
    # test_executions
    ('idx_test_executions_plan_id',     'test_executions',              'test_plan_id'),
    ('idx_test_executions_case_id',     'test_executions',              'test_case_id'),
    ('idx_test_executions_executor_id', 'test_executions',              'executor_id'),
    # reports
    ('idx_reports_test_plan_id',        'reports',                      'test_plan_id'),
    # test_case_zmind_links
    ('idx_zmind_links_case_id',         'test_case_zmind_links',        'test_case_id'),
    ('idx_zmind_links_plan_id',         'test_case_zmind_links',        'test_plan_id'),
    # testcase_history
    ('idx_testcase_history_case_id',    'testcase_history',             'testcase_id'),
    # user_roles
    ('idx_user_roles_user_id',          'user_roles',                   'user_id'),
    ('idx_user_roles_role_id',          'user_roles',                   'role_id'),
    # user_projects
    ('idx_user_projects_user_id',       'user_projects',                'user_id'),
    ('idx_user_projects_project_id',    'user_projects',                'project_id'),
    # user_teams
    ('idx_user_teams_user_id',          'user_teams',                   'user_id'),
    ('idx_user_teams_team_id',          'user_teams',                   'team_id'),
    # team_projects
    ('idx_team_projects_team_id',       'team_projects',                'team_id'),
    ('idx_team_projects_project_id',    'team_projects',                'project_id'),
    # test_plans
    ('idx_test_plans_project_id',       'test_plans',                   'project_id'),
    ('idx_test_plans_reviewer_id',      'test_plans',                   'reviewer_id'),
    # teams
    ('idx_teams_department_id',         'teams',                        'department_id'),
    ('idx_teams_leader_id',             'teams',                        'leader_id'),
    # department_managers
    ('idx_dept_managers_dept_id',       'department_managers',          'department_id'),
    ('idx_dept_managers_user_id',       'department_managers',          'user_id'),
    # user_departments
    ('idx_user_departments_user_id',    'user_departments',             'user_id'),
    ('idx_user_departments_dept_id',    'user_departments',             'department_id'),
    # version_notify_group_members
    ('idx_vng_members_group_id',        'version_notify_group_members', 'group_id'),
    ('idx_vng_members_user_id',         'version_notify_group_members', 'user_id'),
    # notification_recipients
    ('idx_notif_recipients_notif_id',   'notification_recipients',      'notification_id'),
    # zmind_sync_status
    ('idx_zmind_sync_project_id',       'zmind_sync_status',            'project_id'),
]


def run_migration():
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for index_name, table_name, column_name in INDEXES_TO_CREATE:
        # 表不存在则跳过
        if table_name not in existing_tables:
            print(f'  [SKIP] {table_name} 表不存在，跳过 {index_name}')
            continue

        # 通过 inspector 检查索引是否已存在，存在则跳过（不依赖 IF NOT EXISTS 语法）
        existing_indexes = {idx['name'] for idx in inspector.get_indexes(table_name)}
        if index_name in existing_indexes:
            print(f'  [SKIP] {index_name} 已存在，跳过')
            continue

        try:
            sql = f'CREATE INDEX {index_name} ON {table_name}({column_name})'
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            print(f'  [OK] {index_name} ON {table_name}({column_name})')
        except Exception as e:
            print(f'  [ERROR] {index_name}: {e}')


if __name__ == '__main__':
    print('=' * 60)
    print('数据库迁移 - 补全高频查询外键索引')
    print('=' * 60)
    run_migration()
