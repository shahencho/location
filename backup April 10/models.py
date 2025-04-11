from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from database import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50))
    tid = Column(String(10))
    lat = Column(Float)
    lng = Column(Float)
    timestamp = Column(DateTime)
    source_payload = Column(Text)  # Use Text if it's a JSON or large string
