from sqlalchemy.orm import Session
from api.models import User
from api.dependents import SessionLocal, bcrypt_context

"""
Scipt for creating an admin user in the database.
"""


def seed_admin_user():
    db = SessionLocal()
    admin_username = "admin"
    admin_password = "supersecret"

    existing = db.query(User).filter(User.username == admin_username).first()
    if not existing:
        admin_user = User(
            username=admin_username,
            hashed_password=bcrypt_context.hash(admin_password),
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created")
    else:
        print("⚠️ Admin user already exists")

    db.close()

if __name__ == "__main__":
    seed_admin_user()
