from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Models import Base

# For testing or development
username = "aap"  #mysql username
password = "mysql"  #mysql password
schema = "aap"  #mysql schema

DATABASE_URL = f"mysql+mysqlconnector://{username}:{password}@localhost:3306/{schema}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to initialize DB (e.g., when app starts)
def init_db():
    Base.metadata.create_all(bind=engine)

