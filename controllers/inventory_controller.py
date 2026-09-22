from datetime import datetime, timezone
from database import get_db
from models import BloodInventory, BloodGroup
from auth_utils import log_audit, create_notification

class InventoryController:
    @staticmethod
    def get_inventory():
        with get_db() as db:
            inventories = db.query(BloodInventory).join(BloodGroup).order_by(BloodGroup.id.asc()).all()
            total_units = sum(inv.units_available for inv in inventories)
            total_ml = sum(inv.total_ml for inv in inventories)
            low_stock_count = sum(1 for inv in inventories if inv.units_available <= inv.low_stock_threshold)

            return {
                'success': True,
                'total_units': total_units,
                'total_ml': total_ml,
                'low_stock_count': low_stock_count,
                'inventory': [inv.to_dict() for inv in inventories]
            }, 200

    @staticmethod
    def adjust_stock(data):
        blood_group_id = data.get('blood_group_id')
        quantity_change = data.get('quantity_change')  # positive or negative integer
        reason = data.get('reason', 'Manual stock adjustment')
        storage_fridge = data.get('storage_fridge')

        if blood_group_id is None or quantity_change is None:
            return {'success': False, 'message': 'Blood Group ID and Quantity Change are required'}, 400

        try:
            blood_group_id = int(blood_group_id)
            quantity_change = int(quantity_change)
        except ValueError:
            return {'success': False, 'message': 'Invalid number format'}, 400

        with get_db() as db:
            inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == blood_group_id).first()
            if not inv:
                return {'success': False, 'message': 'Inventory record not found for this blood group'}, 404

            new_units = inv.units_available + quantity_change
            if new_units < 0:
                return {'success': False, 'message': f'Cannot deduct {abs(quantity_change)} units. Only {inv.units_available} units available in stock.'}, 400

            inv.units_available = new_units
            inv.total_ml = float(new_units) * 450.0
            if storage_fridge:
                inv.storage_fridge = storage_fridge
            inv.last_updated = datetime.now(timezone.utc)

            bg_name = inv.blood_group.group_name if inv.blood_group else f'ID {blood_group_id}'

            # Check low stock trigger
            if inv.units_available <= inv.low_stock_threshold:
                create_notification(
                    db,
                    title=f"⚠️ Low Stock Alert: {bg_name}",
                    message=f"Stock for {bg_name} is critically low ({inv.units_available} units remaining, threshold: {inv.low_stock_threshold}).",
                    notification_type="low_stock"
                )

            log_audit(db, 'STOCK_ADJUSTED', 'Inventory', f'Adjusted {bg_name} by {quantity_change:+d} units. New balance: {new_units}. Reason: {reason}')
            db.commit()

            return {
                'success': True,
                'message': f'Stock for {bg_name} updated to {new_units} units',
                'inventory': inv.to_dict()
            }, 200

    @staticmethod
    def update_threshold(blood_group_id, threshold):
        try:
            threshold = int(threshold)
            if threshold < 0:
                return {'success': False, 'message': 'Threshold must be >= 0'}, 400
        except ValueError:
            return {'success': False, 'message': 'Threshold must be an integer'}, 400

        with get_db() as db:
            if blood_group_id == 'all' or blood_group_id == 0:
                # update all
                invs = db.query(BloodInventory).all()
                for inv in invs:
                    inv.low_stock_threshold = threshold
                log_audit(db, 'THRESHOLD_UPDATED', 'Inventory', f'Updated global low stock threshold to {threshold}')
                db.commit()
                return {'success': True, 'message': f'Global low stock threshold updated to {threshold} units'}, 200

            inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == int(blood_group_id)).first()
            if not inv:
                return {'success': False, 'message': 'Inventory record not found'}, 404

            inv.low_stock_threshold = threshold
            bg_name = inv.blood_group.group_name if inv.blood_group else ''
            log_audit(db, 'THRESHOLD_UPDATED', 'Inventory', f'Updated threshold for {bg_name} to {threshold}')
            db.commit()

            return {'success': True, 'message': f'Low stock threshold for {bg_name} updated to {threshold}', 'inventory': inv.to_dict()}, 200

    @staticmethod
    def get_low_stock():
        with get_db() as db:
            invs = db.query(BloodInventory).filter(BloodInventory.units_available <= BloodInventory.low_stock_threshold).all()
            return {
                'success': True,
                'count': len(invs),
                'low_stock_items': [inv.to_dict() for inv in invs]
            }, 200
