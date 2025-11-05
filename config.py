import os
from dotenv import load_dotenv

load_dotenv()

MCARD_LOGIN = os.getenv("MCARD_LOGIN")
MCARD_SENHA = os.getenv("MCARD_SENHA")
MCARD_URL = os.getenv("MCARD_URL")