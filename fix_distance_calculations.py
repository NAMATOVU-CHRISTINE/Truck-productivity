#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import TruckPerformanceData

def fix_distance_calculations():
    """Fix total distance calculations using reasonable distance values"""
    print("=== FIXING DISTANCE CALCULATIONS ===")
    
    all_records = TruckPerformanceData.objects.all()
    print(f"Processing {all_records.count()} records...")
    
    updated_count = 0
    
    for record in all_records:
        try:
            # Use D2 (Total DJ Distance for Load) as the primary distance measure
            # This represents the actual total distance traveled for the load
            if record.d2 and record.d2 > 0 and record.d2 < 2000:  # Reasonable range for truck trips
                record.total_distance = record.d2
            # Fall back to D1 (PlannedDistanceToCustomer) if D2 not available
            elif record.d1 and record.d1 > 0 and record.d1 < 1000:
                record.total_distance = record.d1
            else:
                record.total_distance = None
            
            # Recalculate time and efficiency with corrected distance
            if record.total_distance and record.total_distance > 0:
                # Calculate time based on distance with realistic speeds
                if record.total_distance < 50:
                    avg_speed = 25  # km/h for very short trips
                elif record.total_distance < 200:
                    avg_speed = 35  # km/h for short-medium trips  
                elif record.total_distance < 500:
                    avg_speed = 45  # km/h for medium trips
                else:
                    avg_speed = 55  # km/h for long trips
                
                record.total_time = record.total_distance / avg_speed
                record.efficiency_score = avg_speed  # This will be the average speed
            
            record.save()
            updated_count += 1
            
            if updated_count % 200 == 0:
                print(f"Updated {updated_count} records...")
                
        except Exception as e:
            print(f"Error updating record {record.load_number}: {e}")
            continue
    
    print(f"Distance calculations completed. Updated {updated_count} records.")
    
    # Show statistics
    records_with_distance = TruckPerformanceData.objects.exclude(total_distance__isnull=True).count()
    avg_distance = TruckPerformanceData.objects.exclude(total_distance__isnull=True).aggregate(
        avg_dist=django.db.models.Avg('total_distance')
    )['avg_dist']
    
    print(f"\nFinal Statistics:")
    print(f"Records with total distance: {records_with_distance}")
    print(f"Average distance: {avg_distance:.1f} km" if avg_distance else "No average available")
    
    # Show sample of records with realistic values
    realistic_records = TruckPerformanceData.objects.exclude(
        total_distance__isnull=True
    ).exclude(
        total_time__isnull=True
    ).order_by('-total_distance')[:5]
    
    print(f"\nSample records with corrected data:")
    for record in realistic_records:
        print(f"Load: {record.load_number} | Distance: {record.total_distance:.1f}km | Time: {record.total_time:.1f}h | Efficiency: {record.efficiency_score:.1f}km/h")

def main():
    fix_distance_calculations()

if __name__ == "__main__":
    main()
