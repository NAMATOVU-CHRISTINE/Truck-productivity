from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import TruckPerformanceData
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Update truck statuses dynamically for demo purposes'

    def handle(self, *args, **options):
        # Get trucks that are not completed
        active_trucks = TruckPerformanceData.objects.exclude(current_status='journey_completed')
        
        status_progression = [
            'pending_departure',
            'departed_depot', 
            'in_transit',
            'at_customer',
            'servicing_customer',
            'returning_depot',
            'journey_completed'
        ]
        
        updated_count = 0
        
        for truck in active_trucks:
            # Get current status index
            try:
                current_index = status_progression.index(truck.current_status)
            except ValueError:
                current_index = 0
            
            # Randomly decide whether to advance this truck's status
            if random.random() < 0.3:  # 30% chance to advance
                if current_index < len(status_progression) - 1:
                    new_status = status_progression[current_index + 1]
                    truck.current_status = new_status
                    
                    # Update corresponding timestamp fields
                    now = timezone.now()
                    
                    if new_status == 'departed_depot':
                        truck.dj_departure_time = now
                    elif new_status == 'at_customer':
                        truck.arrival_at_customer = now
                    elif new_status == 'servicing_customer':
                        truck.service_start_time = now
                    elif new_status == 'returning_depot':
                        truck.departure_time_from_customer = now
                    elif new_status == 'journey_completed':
                        truck.arrival_at_depot = now
                    
                    truck.save()
                    updated_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated {truck.load_number} to {new_status}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} trucks'
            )
        )
