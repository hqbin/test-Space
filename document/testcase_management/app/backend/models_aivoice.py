from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, BigInteger
from sqlalchemy.sql import func
from database import Base


class AiVoiceReleaseNote(Base):
    __tablename__ = "aivoice_release_notes"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(100), nullable=False, index=True)
    parentVersion = Column(String(100), default="")
    branch = Column(String(200), default="")
    commitHash = Column(String(100), nullable=True)
    commitMessage = Column(Text, nullable=True)
    author = Column(String(100), nullable=False)
    changeDescription = Column(Text, nullable=False)
    affectedModules = Column(Text, default="[]")
    changeType = Column(String(50), default="功能")
    severity = Column(String(20), default="中")
    rdSmokeStatus = Column(String(50), default="未测试")
    testingNotes = Column(Text, nullable=True)
    regressionRisk = Column(Text, nullable=True)
    affectedFeatures = Column(Text, default="[]")
    breakingChanges = Column(Boolean, default=False)
    migrationType = Column(String(50), default="无")
    workspaceId = Column(String(100), default="AI Voice", index=True)
    projectType = Column(String(100), nullable=True, index=True)
    apkFileName = Column(String(255), nullable=True)
    apkFileSize = Column(BigInteger, nullable=True)
    apkFilePath = Column(String(500), nullable=True)
    testReportFileName = Column(String(255), nullable=True)
    testReportFileSize = Column(BigInteger, nullable=True)
    testReportFilePath = Column(String(500), nullable=True)
    fixedPRs = Column(Text, default="[]")
    createdById = Column(Integer, ForeignKey("users.id"), nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiVoiceVersionRecord(Base):
    __tablename__ = "aivoice_version_records"

    id = Column(Integer, primary_key=True, index=True)
    releaseNoteId = Column(String(50), nullable=True, index=True)
    qaEarlyInterventionReason = Column(Text, nullable=True)
    qaEarlyInterventionOwner = Column(String(100), nullable=True)
    versionNumber = Column(String(100), nullable=False, index=True)
    parentVersion = Column(String(100), default="")
    firmwareVersion = Column(String(100), nullable=True)
    linkedIssues = Column(Text, default="[]")
    changeDescription = Column(Text, nullable=False)
    modifiedModules = Column(Text, default="[]")
    riskLevel = Column(String(20), default="中")
    smokeTestResult = Column(String(50), default="未测试")
    voiceRegressionResult = Column(String(50), default="未测试")
    systemRegressionResult = Column(String(50), default="未测试")
    workspaceId = Column(String(100), default="AI Voice", index=True)
    projectType = Column(String(100), nullable=True, index=True)
    testCycle = Column(String(100), nullable=True)
    prototypeSource = Column(String(100), nullable=True)
    prototypeFileName = Column(String(255), nullable=True)
    prototypeFilePath = Column(String(500), nullable=True)
    prototypeFileSize = Column(BigInteger, nullable=True)
    testResultFileName = Column(String(255), nullable=True)
    testResultFilePath = Column(String(500), nullable=True)
    testResultFileSize = Column(BigInteger, nullable=True)
    languageModel = Column(String(100), nullable=True)
    versionStatus = Column(String(50), default="待测试", index=True)
    releaseDecision = Column(String(50), default="待评估")
    conclusionSummary = Column(Text, nullable=True)
    remainingRisks = Column(Text, nullable=True)
    nextActions = Column(Text, nullable=True)
    conclusionOwner = Column(String(100), nullable=True)
    conclusionUpdatedAt = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    createdById = Column(Integer, ForeignKey("users.id"), nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiVoiceCustomerProblem(Base):
    __tablename__ = "aivoice_customer_problems"

    id = Column(Integer, primary_key=True, index=True)
    problemType = Column(String(20), default="qa", index=True)
    issueId = Column(String(100), nullable=True)
    firmwareVersion = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    classification = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=True)
    status = Column(String(50), default="开放", index=True)
    linkedQaProblems = Column(Text, default="[]")
    workspaceId = Column(String(100), default="AI Voice", index=True)
    projectType = Column(String(100), nullable=True, index=True)
    issueCreatedAt = Column(String(50), default="")
    notes = Column(Text, nullable=True)
    createdById = Column(Integer, ForeignKey("users.id"), nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiVoiceVersionIssue(Base):
    __tablename__ = "aivoice_version_issues"

    id = Column(Integer, primary_key=True, index=True)
    versionRecordId = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    precondition = Column(Text, default="")
    testEnvironment = Column(Text, default="")
    status = Column(String(50), default="待处理", index=True)
    severity = Column(String(20), default="中")
    linkedPR = Column(String(255), nullable=True)
    reporter = Column(String(100), nullable=False)
    assignee = Column(String(100), nullable=True)
    resolution = Column(Text, nullable=True)
    attachments = Column(Text, default="[]")
    syncedProblemId = Column(String(50), default="")
    createdById = Column(Integer, ForeignKey("users.id"), nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiVoiceTestCase(Base):
    __tablename__ = "aivoice_test_cases"

    id = Column(Integer, primary_key=True, index=True)
    caseId = Column(String(100), default="")
    caseName = Column(String(255), nullable=False, index=True)
    description = Column(Text, default="")
    precondition = Column(Text, default="")
    steps = Column(Text, default="[]")
    expectedResult = Column(Text, default="")
    category = Column(String(100), nullable=False, index=True)
    module = Column(String(100), default="")
    priority = Column(String(20), default="中")
    workspaceId = Column(String(100), default="AI Voice", index=True)
    projectType = Column(String(100), nullable=True, index=True)
    tags = Column(Text, default="[]")
    createdById = Column(Integer, ForeignKey("users.id"), nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiVoiceSetting(Base):
    __tablename__ = "aivoice_app_settings"

    key = Column(String(255), primary_key=True)
    value = Column(Text, default="")
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiVoiceProjectWorkspace(Base):
    __tablename__ = "aivoice_project_workspaces"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    builtin = Column(Boolean, default=False)
    createdById = Column(Integer, ForeignKey("users.id"), nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiVoiceWorkspaceModule(Base):
    __tablename__ = "aivoice_workspace_modules"

    workspaceId = Column(String(50), primary_key=True)
    moduleId = Column(String(50), primary_key=True)
    createdAt = Column(DateTime, server_default=func.now())


class AiVoiceWorkspaceGroup(Base):
    __tablename__ = "aivoice_workspace_groups"

    id = Column(String(50), primary_key=True)
    workspaceId = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    projectType = Column(String(100), nullable=False)
    builtin = Column(Boolean, default=False)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiRecommendHistory(Base):
    """AI用例推荐历史记录"""
    __tablename__ = "ai_recommend_history"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)  # 推荐标题（用户输入或自动生成）
    releaseNote = Column(Text, nullable=False)  # Release Note 原文
    projectIds = Column(Text, nullable=False, default="[]")  # JSON: 选择的用例库ID列表
    projectNames = Column(Text, default="[]")  # JSON: 用例库名称列表

    # AI 分析结果
    affectedModules = Column(Text, default="[]")  # JSON: 影响模块
    riskLevel = Column(String(20), default="中")  # 风险等级
    testDirections = Column(Text, default="[]")  # JSON: 测试方向
    summary = Column(Text, default="")  # 影响范围摘要

    # 推荐结果
    recommendedCases = Column(Text, default="[]")  # JSON: 推荐用例列表
    recommendedCount = Column(Integer, default=0)  # 推荐用例数量

    # 覆盖率
    coverageRate = Column(Integer, default=0)
    coverageData = Column(Text, default="{}")  # JSON: 完整覆盖率数据

    # AI 补充用例
    supplementCases = Column(Text, default="[]")  # JSON: AI生成的补充用例

    # 套件创建信息
    suiteId = Column(Integer, nullable=True)  # 关联的测试套件ID
    suiteName = Column(String(255), nullable=True)

    # 元数据
    createdById = Column(Integer, ForeignKey("users.id"), nullable=True)
    createdByName = Column(String(100), nullable=True)
    createdAt = Column(DateTime, server_default=func.now())
