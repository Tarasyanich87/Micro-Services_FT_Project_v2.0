# JWT configuration
import os

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
SECRET_KEY = os.getenv("JWT_SECRET", "your-jwt-secret-change-in-production")
