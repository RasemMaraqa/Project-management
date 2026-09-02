from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.permissions import get_workspace_member
from app.db import get_db
from app.dependencies import (
    get_current_user,
    get_task
)

from app.models import (
    User,
    Task,
    Project,
    Workspace,
    TaskPriority,
    TaskStatus
)

from app.permissions import (
    require_project_access,
    Permission,
    require_permission
)
from app.schemas import (
    TaskUpdate,
    TaskResponse,
    TaskCreate,
    TaskListResponse
)

router = APIRouter(
    tags=["Tasks"]
)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse
)
def get_task_endpoint(
    task: Task = Depends(get_task),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    require_project_access(
        task.project,
        current_user,
        db
    )

    return task


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse
)
def update_task(
    task_data: TaskUpdate,
    task: Task = Depends(get_task),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace, member = require_project_access(
        task.project,
        current_user,
        db
    )

    if task_data.assigned_to is not None:
        assigned_user = (
            db.query(User)
            .filter(User.id == task_data.assigned_to)
            .first()
        )

        if not assigned_user:
            raise HTTPException(
                status_code=404,
                detail="Assigned user not found"
            )

        get_workspace_member(
            workspace,
            assigned_user,
            db
        )

    update_data = task_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


@router.delete("/tasks/{task_id}")
def delete_task(
    task: Task = Depends(get_task),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace, member = require_project_access(
        task.project,
        current_user,
        db
    )

    user = get_workspace_member(
        workspace,
        current_user,
        db
        )

    require_permission(
        user,
        Permission.TASK_CREATE
    )

    db.delete(task)
    db.commit()

    return {
        "message": "Task deleted successfully"
    }


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse
         )
def create_task(
    project_id: int,
    taskdata: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == project.workspace_id)
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    get_workspace_member(
        workspace,
        current_user,
        db
    )

    if taskdata.assigned_to is not None:
        assigned_user = (
            db.query(User)
            .filter(User.id == taskdata.assigned_to)
            .first()
        )

        if not assigned_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        get_workspace_member(
            workspace,
            current_user,
            db
        )

    task = Task(
        title=taskdata.title,
        desc=taskdata.desc,
        priority=taskdata.priority,
        due_date=taskdata.due_date,
        assigned_to=taskdata.assigned_to,
        project_id=project_id
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get(
    "/projects/{project_id}/tasks",
    response_model=TaskListResponse
)
def get_tasks(
    project_id: int,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    require_project_access(
        project,
        current_user,
        db
    )

    query = (
        db.query(Task)
        .filter(Task.project_id == project_id)
    )

    if status is not None:
        query = query.filter(
            Task.status == status
        )

    if priority is not None:
        query = query.filter(
                    Task.priority == priority
                )

    '''now the page stuff is from AI'''

    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )

    offset = (page - 1) * limit

    total = query.count()

    tasks = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "items": tasks,
        "page": page,
        "limit": limit,
        "total": total
    }
