"""
HealthOps Studio — Database Seed Script

Populates the database with:
1. Default roles (SuperAdmin, Admin, Manager, Editor, Viewer, Guest)
2. Permissions for each role
3. A default tenant ("Default Organization")
4. A default SuperAdmin user

Run this after applying migrations:
    python -m app.seed

WHY SEED ROLES IN CODE?
Roles and permissions are part of the application logic, not user data.
They should be version-controlled and reproducible across environments.
"""

from app.database import SessionLocal, engine, Base
from app.db_models import Tenant, Role, Permission, User
import uuid

# ── Permission matrix: role → allowed actions ─────────────
# Format: "action:resource"
ROLE_PERMISSIONS = {
    "SuperAdmin": [
        "create:workflow", "read:workflow", "update:workflow", "delete:workflow", "execute:workflow",
        "create:patient", "read:patient", "update:patient", "delete:patient",
        "read:job", "delete:job",
        "create:user", "read:user", "update:user", "delete:user",
        "assign:role",
        "read:audit",
        "generate:project",
        "use:ai",
        "read:ai_usage",
        "manage:tenant",
    ],
    "Admin": [
        "create:workflow", "read:workflow", "update:workflow", "delete:workflow", "execute:workflow",
        "create:patient", "read:patient", "update:patient", "delete:patient",
        "read:job", "delete:job",
        "create:user", "read:user", "update:user",
        "assign:role",
        "read:audit",
        "generate:project",
        "use:ai",
        "read:ai_usage",
    ],
    "Manager": [
        "create:workflow", "read:workflow", "update:workflow", "execute:workflow",
        "create:patient", "read:patient", "update:patient",
        "read:job",
        "generate:project",
        "use:ai",
    ],
    "Editor": [
        "create:workflow", "read:workflow", "update:workflow",
        "create:patient", "read:patient", "update:patient",
        "read:job",
        "generate:project",
        "use:ai",
    ],
    "Viewer": [
        "read:workflow",
        "read:patient",
        "read:job",
    ],
    "Guest": [
        # No permissions — can only access public endpoints
    ],
}


def seed_database():
    """
    Create tables + seed default data.
    Safe to run multiple times (checks for existing data before inserting).
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── Check if already seeded ───────────────────────
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            print("[INFO] Database already seeded. Skipping.")
            return

        # ── Create default tenant ─────────────────────────
        default_tenant = Tenant(
            id=uuid.uuid4(),
            name="Default Organization",
        )
        db.add(default_tenant)
        db.flush()  # Get the tenant ID before creating users
        print("[OK] Created default tenant: 'Default Organization'")

        # ── Create roles + permissions ────────────────────
        roles = {}
        for role_name, perms in ROLE_PERMISSIONS.items():
            role = Role(name=role_name, description=f"{role_name} role")
            db.add(role)
            db.flush()  # Get the role ID

            for perm_str in perms:
                action, resource = perm_str.split(":")
                permission = Permission(
                    role_id=role.id,
                    resource=resource,
                    action=action,
                )
                db.add(permission)

            roles[role_name] = role
            print(f"  [OK] Role '{role_name}' with {len(perms)} permissions")

        # ── Create default SuperAdmin user ────────────────
        # Password: "Admin@12345678" (meets 12-char minimum)
        # Now using Argon2id via the security module
        from app.security import hash_password

        admin_user = User(
            id=uuid.uuid4(),
            username="admin",
            email="admin@healthops.local",
            hashed_password=hash_password("password"),
            role_id=roles["SuperAdmin"].id,
            tenant_id=default_tenant.id,
        )
        db.add(admin_user)
        print("[OK] Created default admin user (admin / password)")


        db.commit()
        print("\n[DONE] Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
