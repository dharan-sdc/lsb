from database import get_db
from models import AuditLog

class AuditController:
    @staticmethod
    def get_logs(module='', action='', search='', limit=100, offset=0):
        with get_db() as db:
            query = db.query(AuditLog)
            if module and module != 'ALL':
                query = query.filter(AuditLog.module == module)
            if action and action != 'ALL':
                query = query.filter(AuditLog.action.ilike(f"%{action}%"))
            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    (AuditLog.details.ilike(term)) |
                    (AuditLog.user_email.ilike(term)) |
                    (AuditLog.action.ilike(term))
                )

            total = query.count()
            logs = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()

            return {
                'success': True,
                'total': total,
                'logs': [l.to_dict() for l in logs]
            }, 200
