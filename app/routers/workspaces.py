from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.permissions import get_workspace_member
from app.db import get_db
from app.dependencies import (
    get_current_user,
)

from app.models import (
    User,
    Workspace,
    WorkspaceMember,
    WorkspaceRole
)
from app.schemas import (
    WorkspaceResponse,
    WorkspaceCreate,
    WorkspaceUpdate,
    MemberCreate,
    MemberResponse
)

from app.permissions import require_workspace_admin

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"]
)


@router.post("", response_model=WorkspaceResponse)
def create_workspace(
    workspace: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    new_workspace = Workspace(
        name=workspace.name,
        owner_id=current_user.id
    )

    db.add(new_workspace)
    db.commit()
    db.refresh(new_workspace)

    member = WorkspaceMember(
        workspace_id=new_workspace.id,
        user_id=current_user.id,
        role=WorkspaceRole.OWNER
    )

    db.add(member)
    db.commit()

    return new_workspace


@router.get("", response_model=list[WorkspaceResponse])
def get_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspaces = (
        db.query(Workspace).join(
            WorkspaceMember,
            Workspace.id == WorkspaceMember.workspace_id
        )
        .filter(WorkspaceMember.user_id == current_user.id)
        .all()
    )

    return workspaces


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = (
            db.query(Workspace).join(
                WorkspaceMember,
                Workspace.id == WorkspaceMember.workspace_id
            )
            .filter(Workspace.id == workspace_id,
                    WorkspaceMember.user_id == current_user.id)
            .first()
        )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceUpdate)
def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
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

    workspace.name = workspace_data.name
    db.commit()
    db.refresh(workspace)

    return workspace

# love u 👾 if u see this


@router.delete("/{workspace_id}")
def delete_workspace(
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

    require_workspace_admin(
            workspace,
            current_user,
            db
        )

    db.delete(workspace)
    db.commit()

    return {"message": "Workspace deleted successfully"}


@router.post("/{workspace_id}/members")
def add_member(
    workspace_id: int,
    member_data: MemberCreate,
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

    user = (
        db.query(User)
        .filter(User.id == member_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    existing_member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == member_data.user_id
        )
        .first()
    )

    if existing_member:
        raise HTTPException(
            status_code=409,
            detail="User is already a member"
        )

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=member_data.user_id,
        role=member_data.role
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return {
        "message": "Member added successfully"
    }


@router.get(
    "/{workspace_id}/members",
    response_model=list[MemberResponse]
)
def get_workspace_members(
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

    members = (
        db.query(WorkspaceMember, User)
        .join(
            User,
            User.id == WorkspaceMember.user_id
        )
        .filter(
            WorkspaceMember.workspace_id == workspace_id
        )
        .all()
    )

    return [
        {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": member.role
        }
        for member, user in members
    ]

