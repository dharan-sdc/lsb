from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from models.base import Base

class Hospital(Base):
    __tablename__ = 'hospitals'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    license_no = Column(String(100), nullable=True)
    address = Column(Text, nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(150), nullable=False)
    contact_person = Column(String(150), nullable=True)
    hospital_type = Column(String(50), default='General')  # Government, Private, Trauma Center, Clinic
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    inventory = relationship('HospitalInventory', back_populates='hospital', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'license_no': self.license_no,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'contact_person': self.contact_person,
            'hospital_type': self.hospital_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
