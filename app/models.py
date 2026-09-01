from app.db import Base
from datetime import datetime
from sqlalchemy import DateTime, String, ForeignKey
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


# i added the emoji not an AI (dont be a nig)


class WorkspaceRole(str, Enum):
    OWNER = "Owner 🎩"
    MEMBER = "Member 🧔"


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

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WorkspaceRole.MEMBER
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
    DONE = "Done ✅"


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
