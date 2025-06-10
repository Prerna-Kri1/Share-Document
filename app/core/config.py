import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
# DB_PASSWORD=
# DB_USER=
# DB_HOST=
# DB_USER=
FILE_DIR = os.getenv("FILE_DIR", "./files")

FERNET_KEY = os.getenv("FERNET_KEY")
fernet = Fernet(FERNET_KEY.encode())

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30