from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import engine, get_db
from app.models import User, Workspace, WorkspaceMember
from app.security import hash_password
from app.schemas import UserCreate, UserResponse, WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate, WorkspaceRole, MemberResponse, MemberCreate
from app.config import settings
from app.schemas import Token
from app.security import create_access_token, verify_password
from app.dependencies import get_current_user
from app.permissions import get_workspace_member, require_workspace_admin
from fastapi.security import OAuth2PasswordRequestForm
from app.models import Project
from app.permissions import get_workspace_member
from app.schemas import ProjectCreate, ProjectResponse


app = FastAPI(title="Project management")

'''hello there its me rasem this msg was written in the first
commit of this project,i hope somebody see it cuz that means
that i have completed my project'''


@app.get("/")
def root():
    return {"message": "Welcome to the Project Management API"}


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "healthy", "database": "connected"}

    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        User.email == user.email
        ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="email already registered"
        )
    existing_username = db.query(User).filter(
            User.username == user.username
            ).first()

    if existing_username:
        raise HTTPException(
                status_code=409,
                detail="username already registered"
            )

    new_user = User(
        email=user.email,
        username=user.username,
        password_hash=hash_password(user.password_hash)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
def Login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
        ):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        user.id,
        settings.secret_key
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/workspaces", response_model=WorkspaceResponse)
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


@app.get("/workspaces", response_model=list[WorkspaceResponse])
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


@app.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
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


@app.patch("/workspace/{workspace_id}", response_model=WorkspaceUpdate)
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


@app.delete("/workspaces/{workspace_id}")
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


@app.post("/workspaces/{workspace_id}/members")
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


@app.get(
    "/workspaces/{workspace_id}/members",
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


@app.post(
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

    get_workspace_member(
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


@app.get(
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
