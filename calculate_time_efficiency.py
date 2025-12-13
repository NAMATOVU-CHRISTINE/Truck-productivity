#!/usr/bin/env python
import os
import django
import pandas as pd

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import TruckPerformanceData

def calculate_missing_time_and_efficiency():
    """Calculate missing total time and efficiency values"""
    print("=== CALCULATING TIME AND EFFICIENCY ===")
    
    # Get records that need calculations - all records without total_time
    records_to_update = TruckPerformanceData.objects.filter(
        total_time__isnull=True
    )
    
    print(f"Found {records_to_update.count()} records needing time calculations")
    
    updated_count = 0
    
    for record in records_to_update:
        try:
            # Method 1: Use departure to depot arrival time difference (with realistic bounds)
            if record.dj_departure_time and record.arrival_at_depot:
                time_diff = record.arrival_at_depot - record.dj_departure_time
                total_hours = time_diff.total_seconds() / 3600
                # Only use if time is reasonable (between 1 hour and 24 hours)
                if total_hours > 1 and total_hours < 24:
                    record.total_time = total_hours
            
            # Method 2: Use service time at customer if available (reasonable bounds)
            if not record.total_time and record.service_time_at_customer and record.service_time_at_customer > 0:
                hours = record.service_time_at_customer / 60.0  # Convert minutes to hours
                if hours > 0.5 and hours < 12:  # Between 30 minutes and 12 hours
                    record.total_time = hours
            
            # Method 3: Calculate based on distance with realistic speed assumptions
            if not record.total_time and record.total_distance and record.total_distance > 0:
                # For local deliveries, assume lower average speed due to city driving, loading/unloading
                if record.total_distance < 100:
                    avg_speed = 25  # km/h for short trips
                elif record.total_distance < 500:
                    avg_speed = 40  # km/h for medium trips
                else:
                    avg_speed = 50  # km/h for long trips
                
                estimated_time = record.total_distance / avg_speed
                record.total_time = estimated_time
            
            # Calculate efficiency if we have both distance and time
            if record.total_distance and record.total_time and record.total_time > 0:
                efficiency = record.total_distance / record.total_time
                # Cap efficiency at reasonable limits (5-80 km/h)
                if efficiency >= 5 and efficiency <= 80:
                    record.efficiency_score = efficiency
                else:
                    record.efficiency_score = None  # Invalid efficiency
            
            record.save()
            updated_count += 1
            
            if updated_count % 100 == 0:
                print(f"Updated {updated_count} records...")
                
        except Exception as e:
            print(f"Error updating record {record.load_number}: {e}")
            continue
    
    print(f"Time and efficiency calculations completed. Updated {updated_count} records.")
    
    # Show statistics
    total_with_time = TruckPerformanceData.objects.exclude(total_time__isnull=True).count()
    total_with_efficiency = TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).count()
    
    print(f"\nFinal Statistics:")
    print(f"Records with total time: {total_with_time}")
    print(f"Records with efficiency scores: {total_with_efficiency}")
    
    # Show sample of records with complete data
    complete_records = TruckPerformanceData.objects.exclude(
        total_time__isnull=True
    ).exclude(
        efficiency_score__isnull=True
    )[:5]
    
    print(f"\nSample records with complete time/efficiency data:")
    for record in complete_records:
        print(f"Load: {record.load_number} | Time: {record.total_time:.2f}h | Distance: {record.total_distance:.1f}km | Efficiency: {record.efficiency_score:.1f}km/h")

def main():
    calculate_missing_time_and_efficiency()

if __name__ == "__main__":
    main()
