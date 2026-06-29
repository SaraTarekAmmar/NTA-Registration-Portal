"""
auth_helpers.py
===============
Shared JWT constants for the front portal middleware.
Does NOT define login routes (those live in auth_login.py).
"""
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
