from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from models.base import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(150), nullable=True)
    action = Column(String(100), nullable=False)
    module = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'action': self.action,
            'module': self.module,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
