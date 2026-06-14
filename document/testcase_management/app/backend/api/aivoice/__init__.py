from fastapi import APIRouter
from . import release_notes, version_records, customer_problems, version_issues, knowledge_base, apk_upload, project_workspaces, settings, ai_recommend

aivoice_router = APIRouter(tags=["AI语音测试"])

aivoice_router.include_router(release_notes.router)
aivoice_router.include_router(version_records.router)
aivoice_router.include_router(customer_problems.router)
aivoice_router.include_router(version_issues.router)
aivoice_router.include_router(knowledge_base.router)
aivoice_router.include_router(apk_upload.router)
aivoice_router.include_router(project_workspaces.router)
aivoice_router.include_router(settings.router)
aivoice_router.include_router(ai_recommend.router)
