from sqlalchemy.orm import DeclarativeBase

# SuperClass of the models, each model will inherit from this class
class Base(DeclarativeBase):
    pass
