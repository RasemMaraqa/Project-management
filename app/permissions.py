from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_project_workspace
from app.models import User, Workspace, WorkspaceMember, Project
from enum import Enum


def get_workspace_member(
    workspace: Workspace,
    user: User,
    db: Session
):
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id
        )
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=403,
            detail="You are not a member of this workspace"
        )

    return member


def require_workspace_admin(
    workspace: Workspace,
    user: User,
    db: Session
):
    member = get_workspace_member(workspace, user, db)

    require_permission(
        member,
        Permission.WORKSPACE_UPDATE
    )
    return member


def require_project_access(
    project: Project,
    current_user: User,
    db: Session
):
    workspace = get_project_workspace(
        project,
        db
    )

    member = get_workspace_member(
        workspace,
        current_user,
        db
    )

    return workspace, member


class Permission(str, Enum):
    WORKSPACE_VIEW = "workspace:view"
    WORKSPACE_UPDATE = "workspace:update"
    WORKSPACE_DELETE = "workspace:delete"

    MEMBER_VIEW = "member:view"
    MEMBER_INVITE = "member:invite"
    MEMBER_REMOVE = "member:remove"
    MEMBER_UPDATE = "member:update"

    PROJECT_VIEW = "project:view"
    PROJECT_UPDATE = "project:update"
    PROJECT_CREATE = "project:create"
    PROJECT_DELETE = "project:delete"

    TASK_VIEW = "task:view"
    TASK_CREATE = "task:create"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"


DEFAULT_ROLE_PERMISSIONS = {
    "Owner": {
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_UPDATE,
        Permission.WORKSPACE_DELETE,

        Permission.MEMBER_VIEW,
        Permission.MEMBER_INVITE,
        Permission.MEMBER_REMOVE,
        Permission.MEMBER_UPDATE,

        Permission.PROJECT_VIEW,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,

        Permission.TASK_VIEW,
        Permission.TASK_CREATE,
        Permission.TASK_UPDATE,
        Permission.TASK_DELETE,
    },
    "Admin": {
        Permission.WORKSPACE_VIEW,
        Permission.WORKSPACE_UPDATE,
        Permission.WORKSPACE_DELETE,

        Permission.MEMBER_VIEW,
        Permission.MEMBER_INVITE,
        Permission.MEMBER_REMOVE,
        Permission.MEMBER_UPDATE,

        Permission.PROJECT_VIEW,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,
        Permission.PROJECT_DELETE,

        Permission.TASK_VIEW,
        Permission.TASK_CREATE,
        Permission.TASK_UPDATE,
        Permission.TASK_DELETE,
    },
    "Member": {
        Permission.WORKSPACE_VIEW,

        Permission.MEMBER_VIEW,

        Permission.PROJECT_VIEW,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,

        Permission.TASK_VIEW,
        Permission.TASK_CREATE,
        Permission.TASK_UPDATE,
    }
}


def has_permission(
    member,
    permission: Permission
) -> bool:
    if not member.role:
        return False

    return any(
        role_permission.name == permission.value
        for role_permission in member.role.permissions
    )


'''testing class'''

'''
class FakeMember:
    role = "Member"


member = FakeMember()

print(
    has_permission(
        member,
        Permission.TASK_VIEW
    )
)

print(
    has_permission(
        member,
        Permission.TASK_DELETE
    )
)
'''


def require_permission(
    member,
    permission: Permission
):
    if not has_permission(member, permission):
        raise HTTPException(
            status_code=403,
            detail=f"you dont have the {permission.value} permissions"
        )
