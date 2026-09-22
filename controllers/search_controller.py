from database import get_db
from models import BloodGroup, BloodInventory, Donor, Hospital

class SearchController:
    @staticmethod
    def search_blood(blood_group_name='', hospital_id=None):
        blood_group_name = (blood_group_name or '').strip().upper()

        with get_db() as db:
            query = db.query(BloodGroup)
            if blood_group_name and blood_group_name != 'ALL':
                query = query.filter(BloodGroup.group_name == blood_group_name)

            blood_groups = query.all()
            results = []

            for bg in blood_groups:
                inv = bg.inventory
                available_units = inv.units_available if inv else 0
                storage_location = inv.storage_fridge if inv else 'Central Blood Bank Storage'

                # Get count of eligible donors for this blood group
                eligible_donors = db.query(Donor).filter(Donor.blood_group_id == bg.id, Donor.status == 'Eligible').count()

                results.append({
                    'blood_group_id': bg.id,
                    'blood_group_name': bg.group_name,
                    'rh_factor': bg.rh_factor,
                    'units_available': available_units,
                    'total_ml': inv.total_ml if inv else 0.0,
                    'low_stock_threshold': inv.low_stock_threshold if inv else 5,
                    'is_in_stock': available_units > 0,
                    'is_low_stock': available_units <= (inv.low_stock_threshold if inv else 5),
                    'storage_location': storage_location,
                    'can_donate_to': bg.can_donate_to,
                    'can_receive_from': bg.can_receive_from,
                    'eligible_donors_count': eligible_donors,
                    'status_message': f'{available_units} units available in {storage_location}' if available_units > 0 else '⚠️ No stock available currently. Contact eligible registered donors.'
                })

            total_found_units = sum(r['units_available'] for r in results)

            return {
                'success': True,
                'query_blood_group': blood_group_name or 'ALL',
                'total_units_found': total_found_units,
                'has_stock': total_found_units > 0,
                'no_stock_message': 'No blood units available for the requested group. Emergency donor contact is recommended.' if total_found_units == 0 else None,
                'results': results
            }, 200
