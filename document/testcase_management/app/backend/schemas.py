from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None
    status: Optional[int] = 1
    position_tag_id: Optional[int] = None

class User(UserBase):
    id: int
    status: int
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_id: Optional[str] = None
    captcha_code: Optional[str] = None

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

class TestCaseBase(BaseModel):
    primary_project_id: int
    case_number: Optional[str] = None  # 用例编号（可选，由系统自动生成）
    module: str  # 模块（必填）
    sub_module: Optional[str] = None  # 子模块（可选）
    name: str  # 用例标题（必填）
    precondition: Optional[str] = None  # 前置条件（可选）
    steps: str  # 操作步骤（必填，JSON格式：[{"step": "步骤1", "expected": "预期1"}, ...]）
    expected_result: str  # 预期结果（必填，保留用于兼容）
    level: str = "L3"  # 用例等级（必填：L1/L2/L3/L4）
    remarks: Optional[str] = None  # 备注（可选）
    automation: Optional[str] = None  # 自动化（可选：Y/N/空）
    status: Optional[str] = None  # 状态（可选：REVIEWED/PENDING/REJECTED/DEPRECATED）
    zmind_id: Optional[str] = None  # Zmind ID（可选，用于关联Zmind系统）
    case_type: Optional[str] = "COMMON"  # 用例类型：COMMON(功能测试), PERFORMANCE(性能测试), SECURITY(安全测试), INTERFACE(接口测试), INSTALL(安装部署), CONFIG(配置相关), COMPATIBILITY(兼容性测试), OTHER(其他)
    
    # 保留字段用于兼容
    tags: Optional[str] = None  # JSON string
    archive_source: Optional[str] = None  # 归档来源
    share_scope: Optional[str] = "NONE"  # NONE, GROUP, CATEGORY, ALL

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseCreateBatch(BaseModel):
    testcases: List[TestCaseCreate]

class TestCase(TestCaseBase):
    id: int
    source: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TestPlanBase(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    start_time: Optional[str] = None  # 日期格式: YYYY-MM-DD (例如: 2024-01-15)
    end_time: Optional[str] = None    # 日期格式: YYYY-MM-DD (例如: 2024-01-31)

class TestPlanCreate(TestPlanBase):
    test_case_ids: Optional[list[int]] = []
    executor_ids: Optional[list[int]] = []

class TestPlan(TestPlanBase):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TestExecutionCreate(BaseModel):
    test_plan_id: int
    test_case_id: int
    result: str
    remarks: Optional[str] = None
    version_info: Optional[str] = None

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    tag: Optional[str] = None  # Tag用于用例编号生成
    status: Optional[int] = 1
    parent_id: Optional[int] = None
    level: Optional[int] = 3  # 1=GROUP, 2=CATEGORY, 3=PRODUCT
    project_type: Optional[str] = "PRODUCT"  # GROUP, CATEGORY, PRODUCT
    group_name: Optional[str] = None
    category_name: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectTree(BaseModel):
    """项目树形结构"""
    id: int
    name: str
    description: Optional[str] = None
    level: int
    project_type: str
    parent_id: Optional[int] = None
    children: Optional[list] = []
    
    class Config:
        from_attributes = True

class TestCaseShareRequest(BaseModel):
    """用例共享请求"""
    target_project_ids: list[int]
    is_editable: Optional[bool] = False

class TestCaseTagCreate(BaseModel):
    """标签创建"""
    name: str
    color: Optional[str] = "#409EFF"
    description: Optional[str] = None

class ReportGenerate(BaseModel):
    test_plan_id: int
    template_id: Optional[int] = 1
    name: str


# ==================== 新增：附件相关 Schema ====================

class AttachmentBase(BaseModel):
    """附件基础模型"""
    file_name: str
    file_size: int
    file_type: str
    description: Optional[str] = None


class AttachmentCreate(AttachmentBase):
    """附件创建模型"""
    execution_id: int


class AttachmentResponse(AttachmentBase):
    """附件响应模型"""
    id: int
    execution_id: int
    file_path: str
    file_extension: str
    upload_time: datetime
    uploader_id: int
    is_deleted: bool
    
    class Config:
        from_attributes = True


# ==================== 新增：评论相关 Schema ====================

class CommentBase(BaseModel):
    """评论基础模型"""
    entity_type: str  # testplan/testcase/execution
    entity_id: int
    content: str
    parent_id: Optional[int] = None


class CommentCreate(CommentBase):
    """评论创建模型"""
    pass


class CommentResponse(CommentBase):
    """评论响应模型"""
    id: int
    author_id: int
    author_name: Optional[str] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    children: Optional[list] = []
    
    class Config:
        from_attributes = True


# ==================== 新增：进度相关 Schema ====================

class ProgressResponse(BaseModel):
    """进度统计响应模型"""
    total: int
    executed: int
    not_executed: int
    passed: int
    failed: int
    blocked: int
    skipped: int
    progress_percentage: float


class ExecutionProgressResponse(BaseModel):
    """执行进度响应模型"""
    testplan_id: int
    user_id: int
    current_testcase_id: Optional[int] = None
    current_index: int
    sort_order: Optional[list] = None
    last_access_time: datetime
    
    class Config:
        from_attributes = True


class ExecutionProgressSave(BaseModel):
    """保存执行进度请求"""
    testplan_id: int
    current_testcase_id: Optional[int] = None
    current_index: int
    sort_order: Optional[list] = None


# ==================== 修改：测试执行相关 Schema ====================

class TestExecutionCreateEnhanced(BaseModel):
    """增强的测试执行创建模型"""
    test_plan_id: int
    test_case_id: int
    result: str  # PASS/Fail/NA/NT/BLOCK/待确认
    remarks: Optional[str] = None
    actual_result: Optional[str] = None
    failure_reason: Optional[str] = None
    version_info: Optional[str] = None


class TestExecutionResponse(BaseModel):
    """测试执行响应模型"""
    id: int
    test_plan_id: int
    test_case_id: int
    executor_id: int
    result: str
    remarks: Optional[str] = None
    actual_result: Optional[str] = None
    failure_reason: Optional[str] = None
    zmind_issue_id: Optional[str] = None
    zmind_issue_url: Optional[str] = None
    executed_at: datetime
    
    class Config:
        from_attributes = True


class BatchExecutionRequest(BaseModel):
    """批量执行请求"""
    test_plan_id: int
    test_case_ids: list[int]
    result: str  # PASS/Fail/NA/NT/BLOCK/待确认


# ==================== 新增：Zmind问题单相关 Schema ====================

class ZmindIssueCreate(BaseModel):
    """Zmind问题单创建请求（已废弃，实际使用 api/zmind.py 中的本地定义）"""
    execution_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: str
    issue_type: Optional[str] = "Bug"
    priority: Optional[str] = "Medium"
    assignee: Optional[str] = None


class ZmindIssueResponse(BaseModel):
    """Zmind问题单响应"""
    issue_id: str
    issue_url: str
    title: str
    status: str


# ==================== 修改：测试用例 Schema ====================

class TestCaseCreateEnhanced(TestCaseBase):
    """增强的测试用例创建模型（已废弃，使用TestCaseCreate）"""
    pass


class TestCaseEnhanced(TestCase):
    """增强的测试用例响应模型（已废弃，使用TestCase）"""
    pass


# ==================== 模块管理相关 Schema ====================

class ModuleBase(BaseModel):
    """模块基础模型"""
    name: str
    tag: Optional[str] = None  # Tag用于用例编号生成
    parent_id: Optional[int] = None
    requirement_link: Optional[str] = None  # 原始需求链接
    rd_owner: Optional[str] = None  # RD负责人

class ModuleCreate(ModuleBase):
    """创建模块"""
    project_id: int

class ModuleUpdate(BaseModel):
    """更新模块"""
    name: Optional[str] = None
    tag: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    requirement_link: Optional[str] = None
    rd_owner: Optional[str] = None

class ModuleResponse(ModuleBase):
    """模块响应"""
    id: int
    project_id: int
    sort_order: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ModuleTreeNode(BaseModel):
    """模块树节点"""
    id: int
    name: str
    parent_id: Optional[int] = None
    sort_order: int
    requirement_link: Optional[str] = None  # 原始需求链接
    rd_owner: Optional[str] = None  # RD负责人
    count: int = 0  # 用例数量
    children: list['ModuleTreeNode'] = []

class ModuleSortRequest(BaseModel):
    """模块排序请求"""
    module_orders: list[dict]  # [{"id": 1, "sort_order": 0}, {"id": 2, "sort_order": 1}, ...]


# ==================== 评审计划 Schemas ====================

class ReviewPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: int
    team_id: Optional[int] = None

class ReviewPlanCreate(ReviewPlanBase):
    reviewer_ids: Optional[list[int]] = None  # 评审人ID列表
    start_time: Optional[datetime] = None  # 开始时间
    end_time: Optional[datetime] = None  # 结束时间

class ReviewPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    reviewer_ids: Optional[list[int]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None

class ReviewPlanResponse(ReviewPlanBase):
    id: int
    status: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AddTestCasesToPlanRequest(BaseModel):
    testcase_ids: list[int]

class ReviewTestCaseRequest(BaseModel):
    result: str  # APPROVED 或 REJECTED
    comment: Optional[str] = None

class BatchReviewRequest(BaseModel):
    testcase_ids: list[int]
    result: str  # APPROVED 或 REJECTED
    comment: Optional[str] = None


# ==================== 用例模板 Schema ====================

class TemplateFieldConfig(BaseModel):
    """模板字段配置"""
    index: int
    original_name: str
    name: str
    required: bool = False
    field_type: str = "string"  # string, text, enum
    enum_values: Optional[list[str]] = None
    format_check: Optional[str] = None  # step_numbering, avoid_fuzzy_words

class CaseTemplateBase(BaseModel):
    """用例模板基础"""
    name: str

class CaseTemplateCreate(CaseTemplateBase):
    """创建模板（文件通过 multipart/form-data 上传）"""
    pass

class CaseTemplateUpdate(BaseModel):
    """更新模板"""
    name: Optional[str] = None
    fields: Optional[list[TemplateFieldConfig]] = None

class CaseTemplateResponse(BaseModel):
    """模板响应"""
    id: int
    project_id: int
    name: str
    file_name: str
    fields: list[TemplateFieldConfig]
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class CaseTemplateListItem(BaseModel):
    """模板列表项"""
    id: int
    name: str
    file_name: str
    is_default: bool
    field_count: int
    created_at: datetime
    created_by_name: Optional[str] = None


# ========== 版本发布 ==========

class VersionItemBase(BaseModel):
    item_type: str  # new/fix/improve/delete/other
    content: str
    sort_order: Optional[int] = 0

class VersionItemCreate(VersionItemBase):
    pass

class VersionItemResponse(VersionItemBase):
    id: int
    version_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class VersionReleaseBase(BaseModel):
    version_number: str
    title: str

class VersionReleaseCreate(VersionReleaseBase):
    items: list[VersionItemCreate] = []

class VersionReleaseUpdate(BaseModel):
    version_number: Optional[str] = None
    title: Optional[str] = None
    items: Optional[list[VersionItemCreate]] = None

class VersionReleaseResponse(VersionReleaseBase):
    id: int
    status: str
    notify_enabled: bool
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: list[VersionItemResponse] = []
    class Config:
        from_attributes = True

class VersionReleasePublishRequest(BaseModel):
    notify_enabled: bool = False
    targets: list[dict] = []  # [{"type": "user", "id": 1}, {"type": "group", "id": 2}]

class VersionInfoResponse(BaseModel):
    id: int
    version_number: str
    title: str
    published_at: Optional[datetime] = None
    items: list[VersionItemResponse] = []
    class Config:
        from_attributes = True


# ========== 版本通知用户组 ==========

class VersionNotifyGroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class VersionNotifyGroupCreate(VersionNotifyGroupBase):
    user_ids: list[int] = []

class VersionNotifyGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class VersionNotifyGroupMemberResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class VersionNotifyGroupResponse(VersionNotifyGroupBase):
    id: int
    created_by: Optional[int] = None
    member_count: int = 0
    members: list[VersionNotifyGroupMemberResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class MoveUsersRequest(BaseModel):
    user_ids: list[int]
    target_group_id: int


# ==================== 任务总览 Schemas ====================

class TaskOverviewCreate(BaseModel):
    project_id: Optional[int] = None
    team_id: int
    name: str
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    plan_ids: Optional[list[int]] = []
    viewer_ids: Optional[list[int]] = []


class TaskOverviewUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    plan_ids: Optional[list[int]] = None
    viewer_ids: Optional[list[int]] = None


class TaskOverviewAddPlans(BaseModel):
    plan_ids: list[int]
