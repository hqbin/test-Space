from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AiVoiceReleaseNoteCreate(BaseModel):
    version: str
    parentVersion: Optional[str] = ""
    branch: Optional[str] = ""
    commitHash: Optional[str] = None
    commitMessage: Optional[str] = None
    author: str
    changeDescription: str
    affectedModules: Optional[List[str]] = None
    changeType: Optional[str] = "功能"
    severity: Optional[str] = "中"
    rdSmokeStatus: Optional[str] = "未测试"
    testingNotes: Optional[str] = None
    regressionRisk: Optional[str] = None
    affectedFeatures: Optional[List[str]] = None
    breakingChanges: Optional[bool] = False
    migrationType: Optional[str] = "无"
    workspaceId: Optional[str] = "AI Voice"
    projectType: Optional[str] = None
    fixedPRs: Optional[List[str]] = None


class AiVoiceReleaseNoteUpdate(BaseModel):
    version: Optional[str] = None
    parentVersion: Optional[str] = None
    branch: Optional[str] = None
    commitHash: Optional[str] = None
    commitMessage: Optional[str] = None
    changeDescription: Optional[str] = None
    affectedModules: Optional[List[str]] = None
    changeType: Optional[str] = None
    severity: Optional[str] = None
    rdSmokeStatus: Optional[str] = None
    testingNotes: Optional[str] = None
    regressionRisk: Optional[str] = None
    affectedFeatures: Optional[List[str]] = None
    breakingChanges: Optional[bool] = None
    migrationType: Optional[str] = None
    projectType: Optional[str] = None
    fixedPRs: Optional[List[str]] = None


class AiVoiceReleaseNote(AiVoiceReleaseNoteCreate):
    id: int
    createdById: Optional[int] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class AiVoiceVersionRecordCreate(BaseModel):
    releaseNoteId: Optional[str] = None
    qaEarlyInterventionReason: Optional[str] = None
    qaEarlyInterventionOwner: Optional[str] = None
    versionNumber: str
    parentVersion: Optional[str] = ""
    firmwareVersion: Optional[str] = None
    linkedIssues: Optional[List[str]] = None
    changeDescription: str
    modifiedModules: Optional[List[str]] = None
    riskLevel: Optional[str] = "中"
    smokeTestResult: Optional[str] = "未测试"
    voiceRegressionResult: Optional[str] = "未测试"
    systemRegressionResult: Optional[str] = "未测试"
    workspaceId: Optional[str] = "AI Voice"
    projectType: Optional[str] = None
    testCycle: Optional[str] = None
    prototypeSource: Optional[str] = None
    languageModel: Optional[str] = None
    notes: Optional[str] = None


class AiVoiceVersionRecordUpdate(BaseModel):
    releaseNoteId: Optional[str] = None
    qaEarlyInterventionReason: Optional[str] = None
    qaEarlyInterventionOwner: Optional[str] = None
    versionNumber: Optional[str] = None
    parentVersion: Optional[str] = None
    firmwareVersion: Optional[str] = None
    linkedIssues: Optional[List[str]] = None
    changeDescription: Optional[str] = None
    modifiedModules: Optional[List[str]] = None
    riskLevel: Optional[str] = None
    smokeTestResult: Optional[str] = None
    voiceRegressionResult: Optional[str] = None
    systemRegressionResult: Optional[str] = None
    projectType: Optional[str] = None
    testCycle: Optional[str] = None
    prototypeSource: Optional[str] = None
    languageModel: Optional[str] = None
    versionStatus: Optional[str] = None
    releaseDecision: Optional[str] = None
    conclusionSummary: Optional[str] = None
    remainingRisks: Optional[str] = None
    nextActions: Optional[str] = None
    conclusionOwner: Optional[str] = None
    notes: Optional[str] = None


class AiVoiceVersionRecord(AiVoiceVersionRecordCreate):
    id: int
    versionStatus: str
    releaseDecision: str
    conclusionOwner: Optional[str] = None
    conclusionUpdatedAt: Optional[datetime] = None
    createdById: Optional[int] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class AiVoiceCustomerProblemCreate(BaseModel):
    problemType: Optional[str] = "qa"
    issueId: Optional[str] = None
    firmwareVersion: Optional[str] = None
    description: str
    classification: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = "开放"
    linkedQaProblems: Optional[List[str]] = None
    workspaceId: Optional[str] = "AI Voice"
    projectType: Optional[str] = None
    issueCreatedAt: Optional[str] = ""
    notes: Optional[str] = None


class AiVoiceCustomerProblemUpdate(BaseModel):
    problemType: Optional[str] = None
    issueId: Optional[str] = None
    firmwareVersion: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = None
    linkedQaProblems: Optional[List[str]] = None
    projectType: Optional[str] = None
    issueCreatedAt: Optional[str] = None
    notes: Optional[str] = None


class AiVoiceCustomerProblem(AiVoiceCustomerProblemCreate):
    id: int
    createdById: Optional[int] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class AiVoiceVersionIssueCreate(BaseModel):
    versionRecordId: str
    title: str
    description: Optional[str] = None
    precondition: Optional[str] = ""
    testEnvironment: Optional[str] = ""
    status: Optional[str] = "待处理"
    severity: Optional[str] = "中"
    linkedPR: Optional[str] = None
    reporter: str
    assignee: Optional[str] = None
    resolution: Optional[str] = None
    attachments: Optional[List[str]] = None
    syncedProblemId: Optional[str] = ""


class AiVoiceVersionIssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    precondition: Optional[str] = None
    testEnvironment: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    linkedPR: Optional[str] = None
    assignee: Optional[str] = None
    resolution: Optional[str] = None
    attachments: Optional[List[str]] = None
    syncedProblemId: Optional[str] = None


class AiVoiceVersionIssue(AiVoiceVersionIssueCreate):
    id: int
    createdById: Optional[int] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class AiVoiceTestCaseCreate(BaseModel):
    caseId: Optional[str] = ""
    caseName: str
    description: Optional[str] = ""
    precondition: Optional[str] = ""
    steps: Optional[List[dict]] = None
    expectedResult: Optional[str] = ""
    category: str
    module: Optional[str] = ""
    priority: Optional[str] = "中"
    workspaceId: Optional[str] = "AI Voice"
    projectType: Optional[str] = None
    tags: Optional[List[str]] = None


class AiVoiceTestCaseUpdate(BaseModel):
    caseName: Optional[str] = None
    description: Optional[str] = None
    precondition: Optional[str] = None
    steps: Optional[List[dict]] = None
    expectedResult: Optional[str] = None
    category: Optional[str] = None
    module: Optional[str] = None
    priority: Optional[str] = None
    projectType: Optional[str] = None
    tags: Optional[List[str]] = None


class AiVoiceTestCase(AiVoiceTestCaseCreate):
    id: int
    createdById: Optional[int] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class AiVoiceProjectWorkspaceCreate(BaseModel):
    id: str
    name: str
    builtin: Optional[bool] = False


class AiVoiceProjectWorkspaceUpdate(BaseModel):
    name: Optional[str] = None


class AiVoiceProjectWorkspace(BaseModel):
    id: str
    name: str
    builtin: bool
    createdById: Optional[int] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class AiVoiceWorkspaceGroupCreate(BaseModel):
    id: str
    workspaceId: str
    name: str
    projectType: str
    builtin: Optional[bool] = False


class AiVoiceWorkspaceGroupUpdate(BaseModel):
    name: Optional[str] = None
    projectType: Optional[str] = None


class AiVoiceWorkspaceGroup(BaseModel):
    id: str
    workspaceId: str
    name: str
    projectType: str
    builtin: bool
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class PagedResponse(BaseModel):
    data: list
    total: int
    page: int
    pageSize: int
    totalPages: int
