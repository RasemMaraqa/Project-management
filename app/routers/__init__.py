from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router
from app.routers.workspaces import router as workspaces_router


__all__ = [
    "projects_router",
    "tasks_router",
    "workspaces_router",
]
