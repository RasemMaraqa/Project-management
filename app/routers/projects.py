from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.permissions import (
    get_workspace_member,
    require_permission,
    Permission as Permissions
    )
from app.db import get_db
from app.dependencies import (
    get_current_user,
)

from app.models import (
    User,
    Project,
    Workspace
)
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate
)


router = APIRouter(
    tags=["Projects"]
)


@router.post(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectResponse
)
def create_project(
    workspace_id: int,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    user = get_workspace_member(
        workspace,
        current_user,
        db
    )
    require_permission(
        user,
        Permissions.PROJECT_CREATE
    )

    project = Project(
        name=project_data.name,
        desc=project_data.desc,
        workspace_id=workspace_id
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get(
    "/workspaces/{workspace_id}/projects",
    response_model=list[ProjectResponse])
def get_projects(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    user = get_workspace_member(
        workspace,
        current_user,
        db
    )
    require_permission(
        user,
        Permissions.PROJECT_VIEW
    )

    projects = (
        db.query(Project)
        .filter(Project.workspace_id == workspace_id)
        .all()
    )

    return projects


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse
)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
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

    user = get_workspace_member(
        workspace,
        current_user,
        db
    )

    require_permission(
        user,
        Permissions.PROJECT_UPDATE
    )

    update_data = project_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
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

    user = get_workspace_member(
        workspace,
        current_user,
        db
    )

    require_permission(
        user,
        Permissions.PROJECT_DELETE
    )

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully"
    }