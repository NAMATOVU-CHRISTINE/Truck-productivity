#!/usr/bin/env python
import os
import django
import pandas as pd
from datetime import datetime, timedelta
import pytz


# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from django.utils import timezone
from dashboard.models import CSVUpload, TruckPerformanceData

def recalculate_time_efficiency():
    """Manually calculate time and efficiency where we have sufficient data"""
    print("=== RECALCULATING TIME AND EFFICIENCY ===")
    
    updated_count = 0
    
    # First, let's use records that have BOTH departure and arrival times for real calculations
    complete_records = TruckPerformanceData.objects.exclude(
        dj_departure_time__isnull=True
    ).exclude(arrival_at_depot__isnull=True)
    print(f"Found {complete_records.count()} records with both departure and arrival times")
    
    for record in complete_records:
        try:
            # Just trigger save to recalculate efficiency with real times
            record.save()
            updated_count += 1
            
            if updated_count <= 10:  # Show first 10 real calculations
                print(f"\nReal calculation for {record.load_number}:")
                print(f"  Departure: {record.dj_departure_time}")
                print(f"  Arrival: {record.arrival_at_depot}")
                print(f"  Total Time: {record.total_time:.2f} hours")
                print(f"  Distance: {record.total_distance} km")
                print(f"  Efficiency: {record.efficiency_score:.1f} km/h")
                
        except Exception as e:
            if updated_count < 5:
                print(f"Error updating {record.load_number}: {e}")
            continue
    
    print(f"\nRecalculated {updated_count} records with real departure/arrival times")
    
    # Now handle records with only arrival times - use more realistic estimation
    print("\n=== PROCESSING RECORDS WITH ARRIVALS ONLY ===")
    depot_arrivals = TruckPerformanceData.objects.exclude(arrival_at_depot__isnull=True).filter(dj_departure_time__isnull=True)
    print(f"Found {depot_arrivals.count()} records with depot arrival times but no departure")
    for record in depot_arrivals:  # Process ALL records, not just first 10
        try:
            # Use delivery time or customer arrival to estimate more realistic departure
            if record.arrival_at_customer and record.arrival_at_depot:
                # If we have customer arrival, use that to estimate departure
                # Assume depot-to-customer is about 60% of total journey time
                total_journey = record.arrival_at_depot - record.arrival_at_customer
                estimated_depot_to_customer = total_journey * 0.6
                estimated_departure = record.arrival_at_customer - estimated_depot_to_customer
                
                record.dj_departure_time = estimated_departure
                record.save()
                updated_count += 1
            elif record.total_distance and record.total_distance > 0:
                # Fallback to distance-based estimation with variable speeds
                # Use different speeds based on distance (longer trips = higher average speed)
                if record.total_distance > 200:
                    avg_speed = 55  # Highway trips
                elif record.total_distance > 100:
                    avg_speed = 50  # Mixed routes
                else:
                    avg_speed = 40  # City/short routes
                
                estimated_hours = record.total_distance / avg_speed
                estimated_departure = record.arrival_at_depot - timedelta(hours=estimated_hours)
                
                record.dj_departure_time = estimated_departure
                record.save()
                updated_count += 1
                    
                if updated_count <= 10:  # Show first 10 updates
                    print(f"\nUpdated {record.load_number}:")
                    print(f"  Estimated Departure: {record.dj_departure_time}")
                    print(f"  Depot Arrival: {record.arrival_at_depot}")
                    print(f"  Calculated Total Time: {record.total_time} hours")
                    print(f"  Distance: {record.total_distance} km")
                    print(f"  Efficiency: {record.efficiency_score} km/h")
                        
        except Exception as e:
            if updated_count < 5:  # Only show first few errors
                print(f"Error updating {record.load_number}: {e}")
            continue
    
    print(f"\nUpdated {updated_count} records with estimated departure times")
    
    # Also handle records with departure times but missing arrivals
    print("\n=== PROCESSING RECORDS WITH DEPARTURES BUT NO ARRIVALS ===")
    departure_only = TruckPerformanceData.objects.exclude(dj_departure_time__isnull=True).filter(arrival_at_depot__isnull=True)
    print(f"Found {departure_only.count()} records with departure times but no depot arrival")
    
    departure_updated = 0
    for record in departure_only:
        try:
            if record.dj_departure_time and record.total_distance and record.total_distance > 0:
                # Use variable speeds based on distance for more realistic estimates
                if record.total_distance > 200:
                    avg_speed = 55  # Highway trips
                elif record.total_distance > 100:
                    avg_speed = 50  # Mixed routes  
                else:
                    avg_speed = 40  # City/short routes
                    
                estimated_hours = record.total_distance / avg_speed
                estimated_arrival = record.dj_departure_time + timedelta(hours=estimated_hours)
                
                # Set the estimated arrival
                record.arrival_at_depot = estimated_arrival
                record.save()  # This will trigger automatic calculation
                departure_updated += 1
                
                if departure_updated <= 10:  # Show first 10
                    print(f"\nUpdated {record.load_number}:")
                    print(f"  Departure: {record.dj_departure_time}")
                    print(f"  Estimated Arrival: {record.arrival_at_depot}")
                    print(f"  Total Time: {record.total_time} hours")
                    print(f"  Efficiency: {record.efficiency_score} km/h")
                    
        except Exception as e:
            if departure_updated < 5:
                print(f"Error updating {record.load_number}: {e}")
            continue
    
    print(f"\nUpdated {departure_updated} records with estimated arrival times")
    
    # Alternative: Use customer arrival times for partial calculations
    print("\\n=== USING CUSTOMER ARRIVAL FOR DELIVERY TIME ===")
    customer_arrivals = TruckPerformanceData.objects.exclude(arrival_at_customer__isnull=True).filter(dj_departure_time__isnull=False)
    print(f"Found {customer_arrivals.count()} records with both departure and customer arrival times")
    
    delivery_updated = 0
    for record in customer_arrivals[:5]:  # Show first 5
        try:
            if record.dj_departure_time and record.arrival_at_customer:
                # Calculate delivery time (departure to customer arrival)
                time_diff = record.arrival_at_customer - record.dj_departure_time
                delivery_hours = time_diff.total_seconds() / 3600
                
                if delivery_hours > 0:  # Sanity check
                    record.delivery_time = delivery_hours
                    record.save()
                    delivery_updated += 1
                    
                    print(f"\\n{record.load_number} - Delivery Time: {delivery_hours:.2f} hours")
                    
        except Exception as e:
            print(f"Error calculating delivery time for {record.load_number}: {e}")
    
    print(f"\\nUpdated delivery times for {delivery_updated} records")
    
    # Final statistics
    print("\\n=== FINAL STATISTICS ===")
    total = TruckPerformanceData.objects.count()
    with_total_time = TruckPerformanceData.objects.exclude(total_time__isnull=True).count()
    with_efficiency = TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).count()
    with_delivery_time = TruckPerformanceData.objects.exclude(delivery_time__isnull=True).count()
    
    print(f"Total records: {total}")
    print(f"Records with total_time: {with_total_time}")
    print(f"Records with efficiency_score: {with_efficiency}")
    print(f"Records with delivery_time: {with_delivery_time}")
    
    # Show sample of records with calculated times
    print("\\n=== SAMPLE RECORDS WITH CALCULATED TIMES ===")
    time_records = TruckPerformanceData.objects.exclude(total_time__isnull=True)[:3]
    for record in time_records:
        print(f"{record.load_number}: {record.total_time:.2f}h, {record.efficiency_score:.1f} km/h")

if __name__ == "__main__":
    recalculate_time_efficiency()
