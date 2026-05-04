"""
database.py - Database Connection Manager

PURPOSE:
This file sets up the SQLAlchemy ORM (Object-Relational Mapping) connection to the MySQL database.
It abstracts away the raw SQL queries, allowing the rest of the application to interact with the 
database using Python objects.

HOW IT WORKS AT A GLANCE:
- Reads the DATABASE_URL from the environment.
- Creates an 'engine' (the core interface to the database).
- Sets up a 'SessionLocal' factory to generate temporary database sessions for each request.
- Exposes a 'get_db()' generator function, which is commonly used as a FastAPI dependency
  to ensure safe database connection handling (opening and closing connections properly).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT CONFIGURATION
load_dotenv()

# Fallback to a default local MySQL connection if DATABASE_URL is not provided in .env
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://crm_admin:admin123@localhost:3306/hcp_crm")

# 2. INITIALIZE ENGINE
# The engine is responsible for managing the connection pool and executing SQL commands.
engine = create_engine(DATABASE_URL)

# 3. CONFIGURE SESSION FACTORY
# autocommit=False: We manually commit transactions (safer).
# autoflush=False: We manually flush changes to the DB before committing.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all our database models (in models.py) will inherit from.
Base = declarative_base()

# 4. DEPENDENCY INJECTION FUNCTION
def get_db():
    """
    Creates a new database session for a request and guarantees it will be closed
    when the request finishes, even if an error occurs.
    This prevents database lockups and connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
