from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from models.base import Base

class BloodUnit(Base):
    __tablename__ = 'blood_units'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_code = Column(String(50), unique=True, nullable=False)  # BU-2026-000101
    blood_group_id = Column(Integer, ForeignKey('blood_groups.id'), nullable=False)
    donation_id = Column(Integer, ForeignKey('blood_donations.id'), nullable=True)
    camp_id = Column(Integer, ForeignKey('blood_camps.id'), nullable=True)
    donor_id = Column(Integer, ForeignKey('donors.id'), nullable=True)
    donor_name = Column(String(150), nullable=True)
    volume_ml = Column(Float, default=450.0, nullable=False)
    collection_date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False)
    expiry_date = Column(Date, default=lambda: (datetime.now(timezone.utc) + timedelta(days=42)).date(), nullable=False)
    source_type = Column(String(50), default='Center Walk-in')  # Blood Camp, Center Walk-in, Mobile Van, Existing System Import
    source_name = Column(String(150), nullable=True)
    storage_location = Column(String(100), default='Main Blood Bank Fridge - Rack A')
    
    # Lifecycle Status: Collected, Testing, Quarantine, Available, Reserved, Issued, Used, Expired, Discarded
    status = Column(String(30), default='Available', nullable=False)
    
    # Testing & Screening Parameters
    test_status = Column(String(30), default='Passed')  # Pending, Passed, Failed, Quarantined
    hiv_test = Column(String(20), default='Negative')   # Negative, Positive, Pending
    hbsag_test = Column(String(20), default='Negative') # Hepatitis B
    hcv_test = Column(String(20), default='Negative')   # Hepatitis C
    vdrl_test = Column(String(20), default='Negative')  # Syphilis
    malaria_test = Column(String(20), default='Negative')
    abo_rh_confirmed = Column(String(20), default='Confirmed')
    
    tested_by = Column(String(120), nullable=True)
    tested_at = Column(DateTime, nullable=True)
    test_notes = Column(Text, nullable=True)
    discard_reason = Column(Text, nullable=True)
    
    assigned_request_id = Column(Integer, ForeignKey('blood_requests.id'), nullable=True)
    assigned_hospital = Column(String(150), nullable=True)
    issue_id = Column(Integer, ForeignKey('blood_issues.id'), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    blood_group = relationship('BloodGroup')
    donation = relationship('BloodDonation')
    camp = relationship('BloodCamp')
    request = relationship('BloodRequest', foreign_keys=[assigned_request_id])

    def to_dict(self):
        today = datetime.now(timezone.utc).date()
        days_to_expiry = (self.expiry_date - today).days if self.expiry_date else 0
        is_expiring_soon = 0 <= days_to_expiry <= 7
        is_expired = days_to_expiry < 0

        return {
            'id': self.id,
            'unit_code': self.unit_code,
            'blood_group_id': self.blood_group_id,
            'blood_group_name': self.blood_group.group_name if self.blood_group else 'Unknown',
            'donation_id': self.donation_id,
            'camp_id': self.camp_id,
            'camp_name': self.camp.name if self.camp else None,
            'donor_id': self.donor_id,
            'donor_name': self.donor_name or (self.donation.donor_name if self.donation else 'Anonymous Donor'),
            'volume_ml': self.volume_ml,
            'collection_date': self.collection_date.isoformat() if self.collection_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'days_to_expiry': days_to_expiry,
            'is_expiring_soon': is_expiring_soon,
            'is_expired': is_expired,
            'source_type': self.source_type,
            'source_name': self.source_name or (self.camp.name if self.camp else 'Central Blood Bank'),
            'storage_location': self.storage_location,
            'status': self.status,
            'test_status': self.test_status,
            'hiv_test': self.hiv_test,
            'hbsag_test': self.hbsag_test,
            'hcv_test': self.hcv_test,
            'vdrl_test': self.vdrl_test,
            'malaria_test': self.malaria_test,
            'abo_rh_confirmed': self.abo_rh_confirmed,
            'tested_by': self.tested_by,
            'tested_at': self.tested_at.isoformat() if self.tested_at else None,
            'test_notes': self.test_notes,
            'discard_reason': self.discard_reason,
            'assigned_request_id': self.assigned_request_id,
            'assigned_hospital': self.assigned_hospital,
            'issue_id': self.issue_id,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
