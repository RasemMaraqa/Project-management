from app.database import SessionLocal
from app.models import Permission as PermissionModel, Role, Workspace
from app.authorization import DEFAULT_ROLE_PERMISSIONS, Permission


def seed_permissions():
    db = SessionLocal()

    try:
        for permission in Permission:
            existing = (
                db.query(PermissionModel)
                .filter(PermissionModel.name == permission.value)
                .first()
            )

            if not existing:
                db.add(
                    PermissionModel(
                        name=permission.value
                    )
                )

        db.commit()

    finally:
        db.close()


def seed_roles():
    db = SessionLocal()

    try:
        workspaces = db.query(Workspace).all()

        for workspace in workspaces:
            for role_name, permissions in DEFAULT_ROLE_PERMISSIONS.items():

                existing = (
                    db.query(Role)
                    .filter(
                        Role.workspace_id == workspace.id,
                        Role.name == role_name
                    )
                    .first()
                    )

                if existing:
                    continue

                role = Role(
                    name=role_name,
                    workspace_id=workspace.id
                )

                for permission in permissions:
                    permission_obj = (
                        db.query(PermissionModel)
                        .filter(
                            PermissionModel.name == permission.value
                        )
                        .first()
                    )

                    if permission_obj:
                        role.permissions.append(permission_obj)

                db.add(role)

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_permissions()
    seed_roles()
    print("DataBase seeded Done")
