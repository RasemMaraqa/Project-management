from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User, Workspace, WorkspaceMember, WorkspaceRole


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

    if member.role not in (
        WorkspaceRole.OWNER,
        WorkspaceRole.ADMIN
    ):
        raise HTTPException(
            status_code=403,
            detail="Admin permission required"
        )

    return member