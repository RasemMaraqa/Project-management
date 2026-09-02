from app.db import Base
from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    owner = relationship("User")
    members = relationship(
        "WorkspaceMember",
        cascade="all, delete-orphan"
    )

    roles: Mapped[list["Role"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan"
    )


# ur here too , nice to meet u mate


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[int] = mapped_column(primary_key=True)

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"),
        nullable=False
    )

    role: Mapped["Role | None"] = relationship(
        back_populates="members"
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    desc: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id"),
        nullable=False
    )


class TaskStatus(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class TaskPriority(str, Enum):
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String[150],
        nullable=False)

    desc: Mapped[str | None] = mapped_column(
        String[1000],
        nullable=False
    )

    status: Mapped[TaskStatus] = mapped_column(
        nullable=False,
        default=TaskStatus.TODO
    )

    priority: Mapped[TaskPriority] = mapped_column(
        nullable=False,
        default=TaskPriority.THREE
    )

    due_date: Mapped[datetime | None] = mapped_column(
        nullable=True
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False
    )

    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    project = relationship("Project")
    assigned_user = relationship(
        "User",
        foreign_keys=[assigned_to]
    )


role_permissions = Table(
    "role_permissions",
    Base.metadata,


    Column(
        "role_id",
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True
    ),


    Column(
        "permission_id",
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True
    )
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )

    workspace: Mapped["Workspace"] = relationship(
        back_populates="roles"
    )

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions",
        back_populates="roles"
    )

    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="role"
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permissions",
        back_populates="permissions"
    )
