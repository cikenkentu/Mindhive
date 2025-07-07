from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Outlet(Base):
    __tablename__ = "outlets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    address = Column(String)
    hours = Column(String)
    services = Column(String) 