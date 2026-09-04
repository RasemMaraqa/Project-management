from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.authorization import (
    Permission,
    get_workspace_member,
    require_workspace_permission,
)
from app.database import get_db
from app.dependencies import (
    get_current_user,
    get_project_task,
    get_workspace,
    get_workspace_project,
)
from app.models import Project, Task, TaskPriority, TaskStatus, User, Workspace
from app.schemas import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate


router = APIRouter(tags=["Tasks"])


def validate_assignee(
    assigned_to: int | None,
    workspace: Workspace,
    db: Session,
) -> None:
    """Ensure an assignee exists and belongs to the task's workspace."""
    if assigned_to is None:
        return

    assignee = db.query(User).filter(User.id == assigned_to).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assigned user not found")

    get_workspace_member(workspace, assignee, db)


@router.get(
    "/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}",
    response_model=TaskResponse,
)
def get_task_endpoint(
    task: Task = Depends(get_project_task),
    workspace: Workspace = Depends(get_workspace),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_workspace_permission(workspace, current_user, Permission.TASK_VIEW, db)
    return task


@router.patch(
    "/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_data: TaskUpdate,
    task: Task = Depends(get_project_task),
    workspace: Workspace = Depends(get_workspace),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_workspace_permission(workspace, current_user, Permission.TASK_UPDATE, db)
    validate_assignee(task_data.assigned_to, workspace, db)

    for field, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/workspaces/{workspace_id}/projects/{project_id}/tasks/{task_id}")
def delete_task(
    task: Task = Depends(get_project_task),
    workspace: Workspace = Depends(get_workspace),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_workspace_permission(workspace, current_user, Permission.TASK_DELETE, db)
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}


@router.post(
    "/workspaces/{workspace_id}/projects/{project_id}/tasks",
    response_model=TaskResponse,
)
def create_task(
    task_data: TaskCreate,
    project: Project = Depends(get_workspace_project),
    workspace: Workspace = Depends(get_workspace),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_workspace_permission(workspace, current_user, Permission.TASK_CREATE, db)
    validate_assignee(task_data.assigned_to, workspace, db)

    task = Task(**task_data.model_dump(), project_id=project.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get(
    "/workspaces/{workspace_id}/projects/{project_id}/tasks",
    response_model=TaskListResponse,
)
def get_tasks(
    project: Project = Depends(get_workspace_project),
    workspace: Workspace = Depends(get_workspace),
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_workspace_permission(workspace, current_user, Permission.TASK_VIEW, db)

    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be greater than 0")
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    query = db.query(Task).filter(Task.project_id == project.id)
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)

    total = query.count()
    tasks = query.offset((page - 1) * limit).limit(limit).all()
    return {"items": tasks, "page": page, "limit": limit, "total": total}
