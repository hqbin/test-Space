from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, BigInteger, JSON, UniqueConstraint, Index
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(255))
    email = Column(String(100))
    full_name = Column(String(100))
    phone = Column(String(20))  # 手机号
    department = Column(String(100))  # 部门/团队
    position_tag_id = Column(Integer, ForeignKey("position_tags.id"))  # 职位Tag关联
    zmind_api_key = Column(String(255))
    avatar = Column(Text)  # 用户头像（base64 data URL）
    must_change_password = Column(Boolean, default=True)  # 首次登录必须修改密码
    status = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PositionTag(Base):
    __tablename__ = "position_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)  # 职位名称
    description = Column(String(255))  # 职位描述
    content_permissions = Column(Text)  # JSON格式存储内容权限
    notification_permissions = Column(Text)  # JSON格式存储通知权限
    is_system = Column(Boolean, default=False)  # 是否为系统预设职位
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    description = Column(String(255))
    permissions = Column(Text)  # JSON格式存储权限列表
    is_system = Column(Boolean, default=False)  # 是否为系统默认角色（不可删除）
    created_at = Column(DateTime, server_default=func.now())

class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    created_at = Column(DateTime, server_default=func.now())

class UserProject(Base):
    __tablename__ = "user_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime, server_default=func.now())

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(Text)
    tag = Column(String(50), nullable=True, index=True)  # Tag用于用例编号生成
    
    # 层级结构字段
    parent_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    level = Column(Integer, default=3)  # 1=小组(GROUP), 2=分类(CATEGORY), 3=产品线(PRODUCT)
    path = Column(String(500), index=True)  # 路径，如 "1/3/5"
    project_type = Column(String(50), default="PRODUCT")  # GROUP, CATEGORY, PRODUCT
    
    # 小组和分类信息（冗余字段，便于查询）
    group_name = Column(String(50))  # 所属小组名称
    category_name = Column(String(50))  # 所属分类名称
    
    status = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)

class TestCase(Base):
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    primary_project_id = Column(Integer, ForeignKey("projects.id"), index=True)  # 主项目（创建时所属）
    
    # 核心字段
    case_number = Column(Text, nullable=False, index=True)  # 用例编号（必填，无长度限制）
    module = Column(Text, nullable=False)  # 模块（必填，无长度限制）
    sub_module = Column(Text, nullable=True)  # 子模块（可选，无长度限制）
    name = Column(Text, nullable=False)  # 用例标题（必填，无长度限制）
    precondition = Column(Text, nullable=True)  # 前置条件（可选）
    steps = Column(Text, nullable=False)  # 操作步骤（必填）
    expected_result = Column(Text, nullable=False)  # 预期结果（必填）
    level = Column(String(10), nullable=False, default="L3", index=True)  # 用例等级
    remarks = Column(Text, nullable=True)  # 备注（可选）
    automation = Column(String(50), nullable=True, index=True)  # 自动化（可选：Y/D/N/N-细分类别/空）
    status = Column(String(20), nullable=True, index=True)  # 状态（可选：REVIEWED/PENDING/REJECTED/DEPRECATED）
    sort_order = Column(Integer, default=0, index=True)  # 排序号（用于自定义排序）
    
    # 用例属性（保留用于兼容）
    case_type = Column(String(50), default="COMMON", index=True)  # COMMON(通用), SPECIFIC(特定)
    priority = Column(String(20), default="MEDIUM")  # 已废弃，保留用于数据迁移
    category = Column(Text)  # 已废弃，使用module替代，无长度限制
    tags = Column(Text)  # JSON格式存储标签
    archive_source = Column(Text, nullable=True)  # 归档来源
    feedback = Column(Text)  # 问题反馈内容
    
    # 共享范围
    share_scope = Column(String(50), default="NONE")  # NONE, GROUP, CATEGORY, ALL
    
    source = Column(String(20), default="LOCAL")
    zmind_id = Column(Text)  # 无长度限制
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)
    updated_by = Column(Integer)

class TestSuite(Base):
    __tablename__ = "test_suites"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class TestSuiteTestCase(Base):
    __tablename__ = "test_suite_test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    test_suite_id = Column(Integer, ForeignKey("test_suites.id"), index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), index=True)
    created_at = Column(DateTime, server_default=func.now())

class TestPlan(Base):
    __tablename__ = "test_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)  # 所属项目组
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=True, index=True)  # 关联套件
    name = Column(String(255))
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(20), default="PENDING")
    reviewer_id = Column(Integer, ForeignKey("users.id"))  # 审核人ID
    zmind_project_id = Column(String(100))  # Zmind项目ID
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)

class TestPlanTestCase(Base):
    __tablename__ = "test_plan_test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"), index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), index=True)
    created_at = Column(DateTime, server_default=func.now())

class TestPlanExecutor(Base):
    __tablename__ = "test_plan_executors"
    
    id = Column(Integer, primary_key=True, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"), index=True)
    executor_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, server_default=func.now())

class TestPlanViewer(Base):
    __tablename__ = "test_plan_viewers"
    
    id = Column(Integer, primary_key=True, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"), index=True)
    viewer_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, server_default=func.now())

class TestExecution(Base):
    __tablename__ = "test_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"))
    test_case_id = Column(Integer, ForeignKey("test_cases.id"))
    executor_id = Column(Integer, ForeignKey("users.id"))
    result = Column(String(20))  # PASS/Fail/NA/NT/BLOCK/待确认
    remarks = Column(Text)
    actual_result = Column(Text, nullable=True)  # 实际结果
    failure_reason = Column(Text, nullable=True)  # 失败原因
    zmind_issue_id = Column(String(100), nullable=True, index=True)  # Zmind问题单ID
    zmind_issue_url = Column(String(500), nullable=True)  # Zmind问题单URL
    executed_at = Column(DateTime, server_default=func.now())
    
    # 用例快照字段 - 保存执行时的用例信息
    testcase_number = Column(String(100))  # 用例编号
    testcase_name = Column(Text)  # 用例标题
    testcase_module = Column(String(200))  # 主模块
    testcase_sub_module = Column(String(200))  # 子模块
    testcase_level = Column(String(10))  # 用例等级
    testcase_precondition = Column(Text)  # 前置条件
    testcase_steps = Column(Text)  # 操作步骤
    testcase_expected_result = Column(Text)  # 预期结果
    
    # PR关联快照 - 保存执行时关联的PR列表（JSON格式）
    pr_links_snapshot = Column(Text)  # 格式: [{"id": "332284", "test_plan_id": 1}, ...]
    
    # 版本信息 - 记录执行时的版本
    version_info = Column(Text, nullable=True)  # 任意文本，不限长度

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"))
    template_id = Column(Integer)
    name = Column(String(255))
    file_path = Column(String(500))
    format = Column(String(20))
    status = Column(String(20), default="PENDING_REVIEW")  # PENDING_REVIEW, APPROVED, REJECTED
    project_name = Column(String(255))
    verify_env = Column(Text)
    release_note = Column(Text)
    zmind_pr_stats = Column(Text)  # JSON: CSV统计结果
    zmind_issue_list = Column(Text)  # JSON: CSV原始issue列表数据
    mplist_data = Column(Text)  # JSON: MpList Excel原始数据
    include_pr_closed = Column(Integer, default=0)  # 0=不统计PR closed, 1=统计
    risk_assessment = Column(Text)  # 风险评估 Risk Assessment（非必填）
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    reject_reason = Column(Text)  # 审核不通过原因
    is_archived = Column(Integer, default=0)  # 归档状态：0=未归档，1=已归档
    archived_at = Column(DateTime)  # 归档时间
    # 快照数据 - 审核通过或拒绝时保存完整报告数据
    snapshot_data = Column(Text)  # JSON: 包含test_results, test_cases, zmind_stats, cover_data等

class TestCaseZmindLink(Base):
    __tablename__ = "test_case_zmind_links"
    
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"))
    zmind_issue_id = Column(String(100))
    zmind_issue_subject = Column(String(500))
    zmind_issue_status = Column(String(50))
    zmind_issue_severity = Column(String(50))
    test_plan_id = Column(Integer, ForeignKey("test_plans.id"))  # 关联的测试计划ID
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer)
    created_by_name = Column(String(50))  # 创建者名称

class ZmindProject(Base):
    __tablename__ = "zmind_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(100), unique=True, index=True)  # 项目标识符
    name = Column(String(255))  # 项目名称（可选）
    description = Column(Text)  # 描述（可选）
    status = Column(Integer, default=1)  # 状态：1=启用，0=禁用
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # 操作用户ID
    username = Column(String(50))  # 用户名（冗余字段，方便查询）
    module = Column(String(50))  # 模块/页面：testcases, testplans, users等
    action = Column(String(50))  # 操作：create, update, delete, import, export等
    description = Column(Text)  # 操作描述
    ip_address = Column(String(50))  # IP地址
    user_agent = Column(String(500))  # 浏览器信息
    request_method = Column(String(10))  # 请求方法：GET, POST, PUT, DELETE
    request_path = Column(String(500))  # 请求路径
    request_params = Column(Text)  # 请求参数（JSON格式）
    response_status = Column(Integer)  # 响应状态码
    created_at = Column(DateTime, index=True)  # 创建时间（在代码中设置为中国时区时间）


class TestCaseProject(Base):
    """测试用例和项目的多对多关联表"""
    __tablename__ = "test_case_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    
    # 关联类型
    relation_type = Column(String(50), default="OWNED")  # OWNED(拥有), SHARED(共享), INHERITED(继承)
    
    # 是否可编辑
    is_editable = Column(Integer, default=1)  # 1=可编辑, 0=只读
    
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer)

class TestCaseTag(Base):
    """测试用例标签表"""
    __tablename__ = "test_case_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    color = Column(String(20), default="#409EFF")
    description = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer)


class TestExecutionAttachment(Base):
    """测试执行附件表"""
    __tablename__ = "test_execution_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)  # 已弃用，保留兼容
    file_data = Column(Text, nullable=True)  # Base64编码的文件数据
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(100), nullable=False)
    file_extension = Column(String(20), nullable=False)
    upload_time = Column(DateTime, nullable=False, server_default=func.now())
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Comment(Base):
    """评论表 - 支持测试计划、测试用例、测试执行的评论"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # testplan/testcase/execution
    entity_id = Column(Integer, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class TestExecutionProgress(Base):
    """测试执行进度表"""
    __tablename__ = "test_execution_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    testplan_id = Column(Integer, ForeignKey("test_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    current_testcase_id = Column(Integer, ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True)
    current_index = Column(Integer, nullable=False, default=0)
    sort_order = Column(JSON, nullable=True)
    last_access_time = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class TestCaseAttachment(Base):
    """测试用例附件表"""
    __tablename__ = "test_case_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)  # 已弃用，保留兼容
    file_data = Column(Text, nullable=True)  # Base64编码的文件数据
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(100), nullable=False)
    file_extension = Column(String(20), nullable=False)
    upload_time = Column(DateTime, nullable=False, server_default=func.now())
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Team(Base):
    """项目组表"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    status = Column(Integer, default=1)  # 1=启用, 0=禁用
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)  # 所属组织
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 项目组负责人
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer)

class UserTeam(Base):
    """用户-项目组关联表"""
    __tablename__ = "user_teams"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    created_at = Column(DateTime, server_default=func.now())

class TeamProject(Base):
    """项目组-用例库关联表"""
    __tablename__ = "team_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime, server_default=func.now())

class TeamLeader(Base):
    """项目组负责人关联表"""
    __tablename__ = "team_leaders"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

# ==================== 组织管理模型 ====================

class Department(Base):
    """部门表"""
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)  # 部门名称
    description = Column(Text)  # 部门描述
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class DepartmentManager(Base):
    """部门负责人关联表"""
    __tablename__ = "department_managers"
    
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

class ProjectGroup(Base):
    """项目组表"""
    __tablename__ = "project_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))  # 项目组名称
    description = Column(Text)  # 项目组描述
    department_id = Column(Integer, ForeignKey("departments.id"))  # 所属部门
    leader_id = Column(Integer, ForeignKey("users.id"))  # 项目组负责人
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserDepartment(Base):
    """用户-部门关联表"""
    __tablename__ = "user_departments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    created_at = Column(DateTime, server_default=func.now())

class UserProjectGroup(Base):
    """用户-项目组关联表"""
    __tablename__ = "user_project_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_group_id = Column(Integer, ForeignKey("project_groups.id"))
    created_at = Column(DateTime, server_default=func.now())

class Module(Base):
    """模块表 - 用于管理测试用例的模块结构"""
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)  # 改为TEXT类型，无长度限制
    tag = Column(String(50), nullable=True, index=True)  # Tag用于用例编号生成
    parent_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=True, index=True)
    sort_order = Column(Integer, nullable=False, default=0, index=True)  # 排序顺序
    requirement_link = Column(Text, nullable=True)  # 原始需求链接
    rd_owner = Column(Text, nullable=True)  # RD负责人，非必填
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)


class TestCaseHistory(Base):
    """测试用例历史记录表"""
    __tablename__ = "testcase_history"
    
    id = Column(Integer, primary_key=True, index=True)
    testcase_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(100), nullable=False)  # 修改的字段名
    old_value = Column(Text)  # 修改前的值
    new_value = Column(Text)  # 修改后的值
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # 修改人ID
    changed_by_name = Column(String(100))  # 修改人姓名（冗余字段，提高查询效率）
    changed_at = Column(DateTime, server_default=func.now())  # 修改时间


# ==================== 通知系统模型 ====================

class Notification(Base):
    """通知记录表"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)  # 通知标题
    content = Column(Text, nullable=False)  # 通知内容
    notification_type = Column(String(50), nullable=False, index=True)  # 通知类型：testcase/testplan/execution/report
    event_type = Column(String(50), nullable=False)  # 事件类型：created/updated/deleted/status_changed等
    related_id = Column(Integer)  # 关联对象ID
    related_type = Column(String(50))  # 关联对象类型
    sender_id = Column(Integer, ForeignKey("users.id"))  # 发送人ID（系统通知为NULL）
    is_system = Column(Boolean, default=True)  # 是否系统通知
    dingtalk_status = Column(String(20))  # 钉钉推送状态: null/pending/sent/failed
    dingtalk_error = Column(Text)  # 钉钉推送失败原因
    created_at = Column(DateTime, server_default=func.now(), index=True)


class NotificationRecipient(Base):
    """通知接收人表"""
    __tablename__ = "notification_recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_read = Column(Boolean, default=False, index=True)  # 是否已读
    read_at = Column(DateTime)  # 阅读时间
    created_at = Column(DateTime, server_default=func.now())


class NotificationRule(Base):
    """通知规则配置表"""
    __tablename__ = "notification_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 规则名称
    description = Column(Text)  # 规则描述
    notification_type = Column(String(50), nullable=False)  # 通知类型
    event_type = Column(String(50), nullable=False)  # 事件类型
    trigger_condition = Column(Text)  # 触发条件（JSON格式）
    recipient_type = Column(String(20), nullable=False)  # 接收人类型：role/user/mixed
    recipient_roles = Column(Text)  # 接收角色列表（JSON格式）
    recipient_users = Column(Text)  # 接收用户列表（JSON格式）
    notification_method = Column(String(20), default='internal')  # 通知方式：internal/dingtalk/both
    template_id = Column(Integer, ForeignKey("notification_templates.id"))  # 模板ID
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NotificationTemplate(Base):
    """通知模板表"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 模板名称
    notification_type = Column(String(50), nullable=False)  # 通知类型
    title_template = Column(String(255), nullable=False)  # 标题模板
    content_template = Column(Text, nullable=False)  # 内容模板
    variables = Column(Text)  # 可用变量列表（JSON格式）
    is_system = Column(Boolean, default=True)  # 是否系统模板
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserNotificationPreference(Base):
    """用户通知偏好设置表"""
    __tablename__ = "user_notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)  # 通知类型：testcase/testplan/execution/report/system
    event_type = Column(String(50), nullable=False, index=True)  # 事件类型：assigned/completed/status_changed等
    is_enabled = Column(Boolean, default=True)  # 是否启用该类型通知
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 添加唯一约束：每个用户的每种通知类型+事件类型只能有一条记录
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_type', 'event_type', name='uq_user_notification_event'),
    )


# ==================== 评审计划模型 ====================

class ReviewPlan(Base):
    """评审计划表"""
    __tablename__ = "review_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # 计划名称
    description = Column(Text)  # 计划描述
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)  # 项目ID
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)  # 所属项目组
    reviewer_ids = Column(Text)  # 评审人ID列表（JSON格式存储）
    start_time = Column(DateTime)  # 开始时间
    end_time = Column(DateTime)  # 结束时间
    status = Column(String(20), nullable=False, default='PENDING', index=True)  # 状态：PENDING/IN_PROGRESS/COMPLETED/CANCELLED
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # 创建人ID
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ReviewPlanTestCase(Base):
    """评审计划-用例关联表"""
    __tablename__ = "review_plan_testcases"

    id = Column(Integer, primary_key=True, index=True)
    review_plan_id = Column(Integer, ForeignKey("review_plans.id", ondelete="CASCADE"), nullable=False, index=True)  # 评审计划ID
    testcase_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, index=True)  # 用例ID
    review_status = Column(String(20), nullable=False, default='PENDING', index=True)  # 评审状态：PENDING/APPROVED/REJECTED
    review_result = Column(String(20))  # 评审结果：APPROVED/REJECTED
    reviewer_id = Column(Integer, ForeignKey("users.id"))  # 评审人ID
    review_comment = Column(Text)  # 评审意见
    reviewed_at = Column(DateTime)  # 评审时间
    testcase_status_snapshot = Column(String(20))  # 用例状态快照（仅用于已完成的评审计划）
    # 草稿字段：评审人在评审页点击"通过/拒绝/废弃"时只更新这些字段，
    # 不直接写入 testcase.status；只有"提交评审计划"时才会升级为正式结论。
    pending_review_result = Column(String(20))  # 草稿结论：APPROVED/REJECTED/DEPRECATED
    pending_review_comment = Column(Text)  # 草稿评审意见
    pending_reviewer_id = Column(Integer, ForeignKey("users.id"))  # 草稿填写人
    pending_reviewed_at = Column(DateTime)  # 草稿填写时间
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class RoleTemplate(Base):
    """角色模板表"""
    __tablename__ = "role_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)  # 模板名称
    description = Column(String(255))  # 模板描述
    permissions = Column(Text)  # JSON格式存储权限列表
    is_system = Column(Boolean, default=False)  # 是否为系统默认模板（不可删除）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ==================== 钉钉机器人配置模型 ====================

class DingtalkBot(Base):
    """钉钉机器人配置表"""
    __tablename__ = "dingtalk_bots"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 机器人名称
    webhook_url = Column(Text, nullable=False)  # Webhook URL
    security_type = Column(String(20), nullable=False, default='keyword')  # 安全方式: keyword/sign
    security_value = Column(Text, nullable=False)  # 关键词或Secret
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)  # 关联项目组
    notification_types = Column(Text, default='[]')  # 关联通知类型（JSON数组）
    is_active = Column(Boolean, default=True)  # 是否启用
    created_by = Column(Integer, ForeignKey("users.id"))  # 创建人
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ==================== 用例校对模型 ====================

class CaseTemplate(Base):
    """用例模板表"""
    __tablename__ = "case_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)  # 改为项目组ID
    name = Column(String(100), nullable=False)  # 模板名称
    file_name = Column(String(255), nullable=False)  # 原始文件名
    file_data = Column(Text, nullable=True)  # Base64编码的原始文件
    fields = Column(Text, nullable=False)  # JSON: 字段配置
    is_default = Column(Boolean, default=False)  # 是否默认模板
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))


# ==================== 测试报告模板模型 ====================

class ReportTemplate(Base):
    """测试报告模板表"""
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    # JSON: 选中的字段列表，如 ["project_name","test_cycle","testers",...]
    selected_fields = Column(Text, nullable=False, default='[]')
    # JSON: 测试标准配置 { "pass_rate_threshold": 95, "criteria_items": ["pass_rate","no_blocker"], "conclusion_pass": "测试通过", "conclusion_fail": "测试未通过" }
    criteria_config = Column(Text, nullable=False, default='{}')
    is_default = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ==================== 登录安全模型 ====================

class LoginAttempt(Base):
    """登录失败记录表 — 用于暴力破解防护"""
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45))  # 支持 IPv6
    success = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


# ==================== 系统配置模型 ====================

class SystemConfig(Base):
    """系统配置表 - 存储可编辑的系统配置项"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)  # 配置键
    config_value = Column(Text)  # 配置值（JSON或纯文本）
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer)  # 最后修改人ID


# ==================== AML Patch 模型 ====================

class AmlPatch(Base):
    """AML Patch表"""
    __tablename__ = "aml_patches"

    id = Column(Integer, primary_key=True, index=True)
    project = Column(String(20), nullable=False)  # 项目: D4/X5/STB
    feature_branch = Column(Text)  # 代码分支
    corresponding_directory = Column(Text)  # 代码路径
    commit_record = Column(Text)  # commit message
    zmind_numbers = Column(Text)  # Zmind号（JSON数组格式存储多个）
    amlogic_jira = Column(Text)  # Amlogic Jira
    patch_provider = Column(Text)  # patch提供人
    is_odm_exclusive = Column(String(10))  # 是否该odm专属: 是/否
    root_cause = Column(Text)  # Root Cause
    patch_solution = Column(Text)  # 解决方案
    impact_scope = Column(Text)  # 推荐测试范围
    aml_sri_result = Column(Text)  # Aml SRI自测结果
    zeasn_merge_record = Column(Text)  # Zeasn合入记录
    remarks = Column(Text)  # 备注
    sync_status = Column(Integer, default=1)  # 同步状态: 1=创建, 2=更新, 3=已同步
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))


class ZmindSyncStatus(Base):
    """Zmind PR同步状态表"""
    __tablename__ = "zmind_sync_status"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(String(20), default="idle")  # idle/syncing/done/failed
    last_synced_at = Column(DateTime)  # 最后完成同步时间
    last_heartbeat = Column(DateTime)  # 最后心跳时间（用于断点续传）
    error_message = Column(Text)  # 错误信息
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AmlProject(Base):
    """AML项目表"""
    __tablename__ = "aml_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)  # 项目名称
    description = Column(String(200))  # 项目描述
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))


class TaskOverview(Base):
    """任务总览表"""
    __tablename__ = "task_overviews"
    __table_args__ = (
        Index("idx_to_team", "team_id"),
        Index("idx_to_status", "status"),
        Index("idx_to_created_by", "created_by"),
        Index("idx_to_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(20), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TaskOverviewPlan(Base):
    """任务总览-测试计划关联表"""
    __tablename__ = "task_overview_plans"
    __table_args__ = (
        UniqueConstraint("task_overview_id", "test_plan_id", name="uq_to_plan"),
        Index("idx_top_plan_id", "test_plan_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    task_overview_id = Column(Integer, ForeignKey("task_overviews.id", ondelete="CASCADE"), nullable=False)
    test_plan_id = Column(Integer, ForeignKey("test_plans.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class TaskOverviewViewer(Base):
    """任务总览-查看人关联表"""
    __tablename__ = "task_overview_viewers"
    __table_args__ = (
        Index("idx_tov_viewer_id", "viewer_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    task_overview_id = Column(Integer, ForeignKey("task_overviews.id", ondelete="CASCADE"), nullable=False)
    viewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class UserBehaviorTracker(Base):
    __tablename__ = "user_behavior_trackers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 用户ID，null表示未登录用户
    username = Column(String(50), nullable=False)  # 用户名
    behavior_type = Column(String(20), nullable=False)  # 行为类型：page_view, click, action
    page_path = Column(String(200), nullable=False)  # 页面路径
    page_name = Column(String(100), nullable=True)  # 页面名称
    action_name = Column(String(100), nullable=True)  # 功能/动作名称（如：新建用例、删除计划）
    action_type = Column(String(50), nullable=True)  # 操作类型（如：create, edit, delete, export）
    element_id = Column(String(100), nullable=True)  # 元素ID
    element_name = Column(String(200), nullable=True)  # 元素描述
    extra_data = Column(Text, nullable=True)  # 额外数据（JSON格式）
    ip_address = Column(String(50), nullable=True)  # IP地址
    user_agent = Column(Text, nullable=True)  # 浏览器信息
    created_at = Column(DateTime, server_default=func.now())  # 行为发生时间


class VersionRelease(Base):
    """版本发布记录表"""
    __tablename__ = "version_releases"

    id = Column(Integer, primary_key=True, index=True)
    version_number = Column(String(50), nullable=False)  # 版本号（如 v1.0.0）
    title = Column(String(200), nullable=False)  # 版本标题
    status = Column(String(20), nullable=False, default="draft")  # 状态：draft/published
    notify_enabled = Column(Boolean, default=False)  # 发布时是否勾选了站内通知
    created_by = Column(Integer, ForeignKey("users.id"))  # 创建人
    published_at = Column(DateTime, nullable=True)  # 发布时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class VersionItem(Base):
    """版本更新条目表"""
    __tablename__ = "version_items"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("version_releases.id", ondelete="CASCADE"), nullable=False)
    item_type = Column(String(20), nullable=False)  # new/fix/improve/delete/other
    content = Column(Text, nullable=False)  # 更新内容描述
    sort_order = Column(Integer, default=0)  # 排序序号
    created_at = Column(DateTime, server_default=func.now())


class VersionNotifyGroup(Base):
    """版本通知用户组表"""
    __tablename__ = "version_notify_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 组名称
    description = Column(String(500))  # 组描述
    created_by = Column(Integer, ForeignKey("users.id"))  # 创建人
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class VersionNotifyGroupMember(Base):
    """版本通知用户组成员表"""
    __tablename__ = "version_notify_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("version_notify_groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class VersionNotifyTarget(Base):
    """版本通知目标表（发布时记录）"""
    __tablename__ = "version_notify_targets"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("version_releases.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(20), nullable=False)  # user/group
    target_id = Column(Integer, nullable=False)  # 用户ID 或 用户组ID
    created_at = Column(DateTime, server_default=func.now())
