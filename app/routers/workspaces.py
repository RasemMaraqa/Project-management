from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.authorization import (
    DEFAULT_ROLE_PERMISSIONS,
    Permission as permission_per,
    get_workspace_member,
    require_permission,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Permission, Role, User, Workspace, WorkspaceMember
from app.schemas import (
    MemberCreate,
    MemberResponse,
    MemberRoleUpdate,
    RoleCreate,
    RoleUpdate,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)


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


@router.get("/permissions")
def get_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    permissions = (
        db.query(Permission)
        .order_by(Permission.id)
        .all()
    )

    return permissions


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

    member = get_workspace_member(
        workspace,
        current_user,
        db
    )

    require_permission(
        member,
        permission_per.ROLE_VIEW
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
        permission_per.WORKSPACE_UPDATE
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
        permission_per.WORKSPACE_DELETE
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
        permission_per.MEMBER_INVITE
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


@router.post("/{workspace_id}/roles")
def create_role(
    workspace_id: int,
    role_data: RoleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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

    member = get_workspace_member(
        workspace,
        current_user,
        db
    )

    require_permission(
        member,
        permission_per.ROLE_CREATE
    )

    existing_role = (
        db.query(Role)
        .filter(
            Role.workspace_id == workspace_id,
            Role.name == role_data.name
        )
        .first()
    )

    if existing_role:
        raise HTTPException(
            status_code=409,
            detail="role already exist"
        )

    role = Role(
        name=role_data.name,
        workspace_id=workspace_id
    )

    permissions = (
        db.query(Permission)
        .filter(
            Permission.id.in_(role_data.permission_ids)
        )
        .all()
    )

    role.permissions = permissions

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


@router.patch("/{workspace_id}/roles/{role_id}")
def update_role(
    workspace_id: int,
    role_id: int,
    role_data: RoleUpdate,
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

    member = get_workspace_member(
        workspace,
        current_user,
        db
    )

    require_permission(
        member,
        permission_per.ROLE_UPDATE
    )

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id,
            Role.workspace_id == workspace_id
        )
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    update_data = role_data.model_dump(exclude_unset=True)

    if "name" in update_data:
        existing_role = (
            db.query(Role)
            .filter(
                Role.workspace_id == workspace_id,
                Role.name == update_data["name"],
                Role.id != role_id
            )
            .first()
        )

        if existing_role:
            raise HTTPException(
                status_code=409,
                detail="A role with this name already exists"
            )

        role.name = update_data["name"]

    if "permission_ids" in update_data:
        permissions = (
            db.query(Permission)
            .filter(
                Permission.id.in_(
                    update_data["permission_ids"]
                )
            )
            .all()
        )

        role.permissions = permissions

    db.commit()
    db.refresh(role)

    return role


@router.delete("/{workspace_id}/roles/{role_id}")
def delete_role(
    workspace_id: int,
    role_id: int,
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

    member = get_workspace_member(
        workspace,
        current_user,
        db
    )

    require_permission(
        member,
        permission_per.ROLE_DELETE
    )

    role = (
        db.query(Role)
        .filter(
            Role.id == role_id,
            Role.workspace_id == workspace_id
        )
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    members = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.role_id == role.id
            )
        .first()
            )

    if members:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a role that is assigned to members"
        )
    db.delete(role)
    db.commit()

    return {
        "message": "Role deleted successfully"
    }


@router.patch("/{workspace_id}/members/{user_id}/role")
def update_member_role(
    workspace_id: int,
    user_id: int,
    role_data: MemberRoleUpdate,
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
        permission_per.MEMBER_UPDATE
    )

    target_member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
        .first()
    )

    if not target_member:
        raise HTTPException(
            status_code=404,
            detail="Workspace member not found"
        )

    role = (
        db.query(Role)
        .filter(
            Role.id == role_data.role_id,
            Role.workspace_id == workspace_id
        )
        .first()
    )

    if not role:
        raise HTTPException(
            status_code=400,
            detail="Role does not belong to this workspace"
        )

    target_member.role_id = role.id

    db.commit()
    db.refresh(target_member)

    return target_member
