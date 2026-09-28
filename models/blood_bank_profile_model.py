from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from models.base import Base

class BloodBankProfile(Base):
    __tablename__ = 'blood_bank_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    bank_name = Column(String(150), nullable=False, default='LSB² Central Blood Bank & Transfusion Center')
    license_number = Column(String(100), default='BB-LIC-2026-98764')
    bank_type = Column(String(100), default='Central Transfusion Center')  # Regional Blood Bank, Hospital Blood Bank, Red Cross Branch
    operating_hours = Column(String(100), default='24/7 Emergency Transfusion Services')
    contact_person = Column(String(120), default='Dr. Robert Hayes, MD (Head of Blood Transfusion)')
    phone = Column(String(50), default='+1 (555) 987-6543')
    emergency_helpline = Column(String(50), default='+1 (800) 555-BLOOD')
    email = Column(String(150), default='contact@lsb2-bloodbank.org')
    website = Column(String(200), default='https://lsb2-bloodbank.org')
    address = Column(Text, default='450 Metro Health Boulevard, Medical District Suite 300')
    city = Column(String(100), default='Metropolis')
    state = Column(String(100), default='State')
    postal_code = Column(String(20), default='10001')
    verification_status = Column(String(30), default='Verified')  # Verified, Pending, Under Review
    verification_docs = Column(Text, default='National Blood Transfusion License.pdf, Quality Assurance Certificate ISO-15189.pdf')
    total_capacity_units = Column(Integer, default=5000)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bank_name': self.bank_name,
            'license_number': self.license_number,
            'bank_type': self.bank_type,
            'operating_hours': self.operating_hours,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'emergency_helpline': self.emergency_helpline,
            'email': self.email,
            'website': self.website,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'verification_status': self.verification_status,
            'verification_docs': self.verification_docs,
            'total_capacity_units': self.total_capacity_units,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
