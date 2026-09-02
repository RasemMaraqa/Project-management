from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.permissions import get_workspace_member, DEFAULT_ROLE_PERMISSIONS
from app.db import get_db
from app.dependencies import (
    get_current_user,
)

from app.models import (
    User,
    Workspace,
    WorkspaceMember,
    Role,
    Permission,
)
from app.schemas import (
    WorkspaceResponse,
    WorkspaceCreate,
    WorkspaceUpdate,
    MemberCreate,
    MemberResponse
)

from app.permissions import require_permission

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"]
)


@router.post(
    "/workspaces",
    response_model=WorkspaceResponse
)
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
    db.flush()

    permissions = {}

    for permission in DEFAULT_ROLE_PERMISSIONS["Owner"]:
        permission_model = (
            db.query(Permission)
            .filter(Permission.name == permission.value)
            .first()
        )

        if not permission_model:
            permission_model = Permission(name=permission.value)
            db.add(permission_model)

        permissions[permission] = permission_model

    db.flush()

    roles = {}

    for role_name in DEFAULT_ROLE_PERMISSIONS:
        role = Role(
            name=role_name,
            workspace_id=new_workspace.id
        )

        db.add(role)
        role.permissions.extend(
            permissions[permission]
            for permission in DEFAULT_ROLE_PERMISSIONS[role_name]
        )
        roles[role_name] = role

    db.flush()

    member = WorkspaceMember(
        workspace_id=new_workspace.id,
        user_id=current_user.id,
        role_id=roles["Owner"].id
    )

    db.add(member)

    db.commit()
    db.refresh(new_workspace)

    return new_workspace


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


@router.get("/{workspace_id}/roles")
def get_workspace_roles(
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
            detail="workspace not found"
        )

    get_workspace_member(
        workspace,
        current_user,
        db
    )

    roles = (
        db.query(Role)
        .filter(Role.workspace_id == workspace_id)
        .all()
    )
    return roles


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
    user = get_workspace_member(
        workspace,
        current_user,
        db
    )
    require_permission(
        user,
        Permission.WORKSPACE_UPDATE
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

    user = get_workspace_member(
        workspace,
        current_user,
        db
    )
    require_permission(
        user,
        Permission.WORKSPACE_DELETE
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
    current_member = get_workspace_member(
        workspace,
        current_user,
        db
    )

    require_permission(
        current_member,
        Permission.MEMBER_INVITE
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

    role = (
        db.query(Role)
        .filter(
            Role.id == member_data.role_id,
            Role.workspace_id == workspace_id
        )
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=400,
            detail="Role does not belong to this workspace"
        )

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=member_data.user_id,
        role_id=role.id
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
            "role": member.role.name if member.role else None
        }
        for member, user in members
    ]
