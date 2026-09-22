from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from models.base import Base

class BloodDonation(Base):
    __tablename__ = 'blood_donations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    donation_code = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    donor_id = Column(Integer, ForeignKey('donors.id'), nullable=True)
    donor_name = Column(String(150), nullable=True)
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=False)
    quantity_units = Column(Integer, default=1, nullable=False)
    quantity_ml = Column(Float, default=450.0, nullable=False)
    donation_date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False)
    blood_pressure = Column(String(30), nullable=True)  # e.g., "120/80"
    hemoglobin = Column(Float, nullable=True)  # e.g., 14.2 g/dL
    pulse_rate = Column(Integer, nullable=True)
    status = Column(String(20), default='Completed')  # Completed, Scheduled, Screened, Discarded
    remarks = Column(Text, nullable=True)
    recorded_by = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship('User', foreign_keys=[user_id])
    donor = relationship('Donor', foreign_keys=[donor_id], back_populates='donations')
    blood_group = relationship('BloodGroup')

    def to_dict(self):
        resolved_name = 'Unknown'
        if self.donor_name:
            resolved_name = self.donor_name
        elif self.user:
            resolved_name = self.user.name
        elif self.donor:
            resolved_name = self.donor.name

        return {
            'id': self.id,
            'donation_code': self.donation_code,
            'user_id': self.user_id,
            'donor_id': self.donor_id,
            'donor_name': resolved_name,
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'quantity_units': self.quantity_units,
            'quantity_ml': self.quantity_ml,
            'donation_date': self.donation_date.isoformat() if self.donation_date else None,
            'blood_pressure': self.blood_pressure,
            'hemoglobin': self.hemoglobin,
            'pulse_rate': self.pulse_rate,
            'status': self.status,
            'remarks': self.remarks,
            'recorded_by': self.recorded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
