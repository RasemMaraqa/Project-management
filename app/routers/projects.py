from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.permissions import get_workspace_member
from app.db import get_db
from app.dependencies import (
    get_current_user,
)

from app.models import (
    User,
    Project,
    Workspace,
)
from app.schemas import (
    ProjectCreate,
    ProjectResponse,
)

from app.permissions import require_workspace_admin

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

    require_workspace_admin(
        workspace,
        current_user,
        db
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

    get_workspace_member(
        workspace,
        current_user,
        db
    )

    projects = (
        db.query(Project)
        .filter(Project.workspace_id == workspace_id)
        .all()
    )

    return projects
