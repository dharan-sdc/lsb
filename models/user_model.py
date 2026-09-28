from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
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
    city = Column(String(100), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    dob = Column(String(30), nullable=True)
    is_blood_group_verified = Column(Boolean, default=False)
    is_donor = Column(Boolean, default=False)  # Willing/Registered voluntary donor flag
    hospital_id = Column(Integer, ForeignKey('hospitals.id'), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    blood_group = relationship('BloodGroup', foreign_keys=[blood_group_id])
    hospital = relationship('Hospital', foreign_keys=[hospital_id])

    def to_dict(self):
        bg_name = None
        if self.blood_group_id:
            try:
                bg_name = self.blood_group.group_name if self.blood_group else None
            except Exception:
                bg_name = None

        hosp_name = None
        if self.hospital_id:
            try:
                hosp_name = self.hospital.name if self.hospital else None
            except Exception:
                hosp_name = None

        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'phone': self.phone,
            'blood_group_id': self.blood_group_id,
            'blood_group_name': bg_name,
            'age': self.age,
            'gender': self.gender,
            'dob': self.dob,
            'city': self.city,
            'address': self.address,
            'emergency_contact': self.emergency_contact,
            'is_blood_group_verified': bool(self.is_blood_group_verified),
            'is_donor': bool(self.is_donor),
            'hospital_id': self.hospital_id,
            'hospital_name': hosp_name,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
