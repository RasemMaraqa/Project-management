from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models import TaskPriority, TaskStatus


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password_hash: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password_hash: str


class Token(BaseModel):
    access_token: str
    token_type: str


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    owner_id: int

    class Config:
        from_attributes = True


class WorkspaceUpdate(BaseModel):
    name: str


class MemberCreate(BaseModel):
    user_id: int
    role_id: int


class MemberResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    role: str


class ProjectCreate(BaseModel):
    name: str
    desc: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    desc: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    desc: str | None
    workspace_id: int

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    desc: str | None = None
    priority: TaskPriority = TaskPriority.THREE
    due_date: datetime | None = None
    assigned_to: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    desc: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assigned_to: int | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    desc: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    project_id: int
    assigned_to: int | None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    page: int
    limit: int
    total: int


class RoleCreate(BaseModel):
    name: str
    permission_ids: list[int] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    permissions_ids: list[int] | None = None


class MemberRoleUpdate(BaseModel):
    role_id: int
