from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='User')  # User, Hospital, BloodBank, Admin
    status = Column(String(20), nullable=False, default='Active')  # Active, Inactive, Suspended
    phone = Column(String(30), nullable=True)
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)  # Male, Female, Other
    address = Column(Text, nullable=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    blood_group = relationship('BloodGroup', foreign_keys=[blood_group_id])
    hospital = relationship('Hospital', foreign_keys=[hospital_id])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'phone': self.phone,
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else None,
            'age': self.age,
            'gender': self.gender,
            'address': self.address,
            'hospital_id': self.hospital_id,
            'hospital_name': self.hospital.name if self.hospital else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
