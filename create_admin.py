from app.models.doc_models import User
from app.database import SessionLocal
from app.utils.security import get_password_hash

def create_admin():
    db = SessionLocal()
    admin = User(username="admin", email="admin@example.com", hashed_password=get_password_hash("securepassword"), role="admin")
    db.add(admin)
    db.commit()
    db.close()

if __name__ == "__main__":
    create_admin()
