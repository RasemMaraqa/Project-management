"""replace legacy workspace member roles with role relationships

Revision ID: b3c4d5e6f7a8
Revises: 19f25cea60cc
Create Date: 2026-09-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b3c4d5e6f7a8"
down_revision = "19f25cea60cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    member_columns = {
        column["name"]
        for column in sa.inspect(bind).get_columns("workspace_members")
    }

    permission_names = (
        "workspace:view", "workspace:update", "workspace:delete",
        "member:view", "member:invite", "member:remove", "member:update",
        "project:view", "project:create", "project:update", "project:delete",
        "task:view", "task:create", "task:update", "task:delete",
    )

    for name in permission_names:
        op.execute(
            sa.text(
                "INSERT INTO permissions (name) VALUES (:name) "
                "ON CONFLICT (name) DO NOTHING"
            ).bindparams(name=name)
        )

    for name in ("Owner", "Admin", "Member"):
        op.execute(
            sa.text(
                "INSERT INTO roles (name, workspace_id) "
                "SELECT :name, id FROM workspaces "
                "ON CONFLICT (workspace_id, name) DO NOTHING"
            ).bindparams(name=name)
        )

    for role_name, role_permissions in {
        "Owner": permission_names,
        "Admin": permission_names,
        "Member": (
            "workspace:view", "member:view", "project:view", "project:create",
            "project:update", "task:view", "task:create", "task:update",
        ),
    }.items():
        for permission_name in role_permissions:
            op.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "SELECT roles.id, permissions.id "
                    "FROM roles, permissions "
                    "WHERE roles.name = :role_name "
                    "AND permissions.name = :permission_name "
                    "ON CONFLICT (role_id, permission_id) DO NOTHING"
                ).bindparams(
                    role_name=role_name,
                    permission_name=permission_name
                )
            )

    if "role" in member_columns:
        op.execute(
            "UPDATE workspace_members AS member "
            "SET role_id = roles.id "
            "FROM roles "
            "WHERE roles.workspace_id = member.workspace_id "
            "AND roles.name = CASE "
            "WHEN member.role IN ('Owner', 'OWNER') THEN 'Owner' "
            "WHEN member.role IN ('Admin', 'ADMIN') THEN 'Admin' "
            "ELSE 'Member' END"
        )
    op.alter_column("workspace_members", "role_id", nullable=False)

    if "role" in member_columns:
        op.drop_column("workspace_members", "role")


def downgrade() -> None:
    op.add_column(
        "workspace_members",
        sa.Column("role", sa.String(length=20), nullable=True)
    )
    op.execute(
        "UPDATE workspace_members AS member "
        "SET role = roles.name FROM roles "
        "WHERE roles.id = member.role_id"
    )
    op.alter_column("workspace_members", "role", nullable=False)
