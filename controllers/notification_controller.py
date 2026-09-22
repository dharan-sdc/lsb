from database import get_db
from models import Notification

class NotificationController:
    @staticmethod
    def list_notifications(unread_only=False):
        with get_db() as db:
            query = db.query(Notification)
            if unread_only:
                query = query.filter(Notification.is_read == False)
            notifs = query.order_by(Notification.created_at.desc()).all()
            unread_count = db.query(Notification).filter(Notification.is_read == False).count()

            return {
                'success': True,
                'unread_count': unread_count,
                'count': len(notifs),
                'notifications': [n.to_dict() for n in notifs]
            }, 200

    @staticmethod
    def mark_read(notification_id):
        with get_db() as db:
            notif = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notif:
                return {'success': False, 'message': 'Notification not found'}, 404

            notif.is_read = True
            db.commit()
            return {'success': True, 'message': 'Notification marked as read', 'notification': notif.to_dict()}, 200

    @staticmethod
    def mark_all_read():
        with get_db() as db:
            db.query(Notification).update({Notification.is_read: True})
            db.commit()
            return {'success': True, 'message': 'All notifications marked as read'}, 200

    @staticmethod
    def delete_notification(notification_id):
        with get_db() as db:
            notif = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notif:
                return {'success': False, 'message': 'Notification not found'}, 404

            db.delete(notif)
            db.commit()
            return {'success': True, 'message': 'Notification deleted'}, 200

    @staticmethod
    def clear_all():
        with get_db() as db:
            db.query(Notification).delete()
            db.commit()
            return {'success': True, 'message': 'All notifications cleared'}, 200
