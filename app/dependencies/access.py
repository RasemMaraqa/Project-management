from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core import ALGORITHM, settings
from app.database import get_db
from app.models import User, Project, Task, Workspace


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise credentials_exception

    return user


def get_workspace(
    workspace_id: int,
    db: Session = Depends(get_db)
) -> Workspace:
    workspace = (
        db.query(Workspace)
        .filter(
            Workspace.id == workspace_id
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found"
        )

    return workspace


def get_workspace_project(
    project_id: int,
    workspace: Workspace = Depends(get_workspace),
    db: Session = Depends(get_db)
) -> Project:
    """Resolve a project only when it belongs to the URL's workspace."""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.workspace_id == workspace.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found in this workspace")
    return project


def get_project_task(
    task_id: int,
    project: Project = Depends(get_workspace_project),
    db: Session = Depends(get_db)
) -> Task:
    """Resolve a task only when it belongs to the URL's project."""
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.project_id == project.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in this project")
    return task
