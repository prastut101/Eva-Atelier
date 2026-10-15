from getpass import getpass
from backend.app.database import SessionLocal
from backend.app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

username = input("Choose admin username: ").strip()
password = getpass("Choose a strong admin password: ")
confirm = getpass("Confirm password: ")

if not username:
    raise SystemExit("Username cannot be empty.")

if len(password) < 12:
    raise SystemExit("Use at least 12 characters for the password.")

if password != confirm:
    raise SystemExit("Passwords do not match.")

if len(password.encode("utf-8")) > 72:
    raise SystemExit("Password must not exceed 72 UTF-8 bytes.")

db = SessionLocal()

try:
    if db.query(User).filter(User.username == username).first():
        raise SystemExit("That username already exists.")

    admin = User(
        username=username,
        hashed_password=pwd_context.hash(password),
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    print(f"Admin account created successfully: {username}")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
