#!/usr/bin/env python
import os
import django
import pandas as pd
from datetime import datetime
import pytz

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from django.utils import timezone
from dashboard.models import TruckPerformanceData

def parse_datetime_flexible(date_str):
    """Parse datetime string in various formats"""
    if pd.isna(date_str) or not date_str:
        return None
    
    # Common formats in the CSV files
    formats = [
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y %H:%M:%S', 
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%d-%m-%Y %H:%M',
        '%d-%m-%Y %H:%M:%S'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(str(date_str).strip(), fmt)
            # Make timezone aware (assume UTC for now)
            return timezone.make_aware(dt, pytz.UTC)
        except ValueError:
            continue
    
    print(f"Could not parse datetime: {date_str}")
    return None

def fix_efficiency_with_real_times():
    """Use original CSV timing data to calculate real efficiency scores"""
    print("=== FIXING EFFICIENCY WITH REAL TIMING DATA ===")
    
    # Load original CSV files
    print("Loading original CSV files...")
    
    # Depot departures - real departure times
    try:
        depot_df = pd.read_csv('media/uploads/1.Depot_Departures_Inf_1752480585396.csv')
        print(f"Loaded {len(depot_df)} depot departure records")
    except Exception as e:
        print(f"Error loading depot departures: {e}")
        return
    
    # Customer timestamps - real customer arrival times  
    try:
        customer_df = pd.read_csv('media/uploads/2.Customer_Timestamps__1752480054194.csv')
        print(f"Loaded {len(customer_df)} customer timestamp records")
    except Exception as e:
        print(f"Error loading customer timestamps: {e}")
        return
    
    # Timestamps and duration - real depot arrival times
    try:
        duration_df = pd.read_csv('media/uploads/4.Timestamps_and_Durat_1752480667772.csv')
        print(f"Loaded {len(duration_df)} duration records")
    except Exception as e:
        print(f"Error loading duration data: {e}")
        return
    
    updated_count = 0
    efficiency_updated = 0
    
    # Get all records with distance data
    records_with_distance = TruckPerformanceData.objects.exclude(total_distance__isnull=True).filter(total_distance__gt=0)
    print(f"Processing {records_with_distance.count()} records with distance data...")
    
    for record in records_with_distance:
        try:
            updated = False
            
            # Find real departure time from depot departures CSV
            depot_match = depot_df[depot_df['Load Name'] == record.load_number]
            real_departure = None
            if not depot_match.empty:
                dep_time_str = depot_match.iloc[0]['DJ Departure Time']
                real_departure = parse_datetime_flexible(dep_time_str)
                if real_departure and real_departure != record.dj_departure_time:
                    record.dj_departure_time = real_departure
                    updated = True
            
            # Find real depot arrival time from duration CSV
            duration_match = duration_df[duration_df['load_name'] == record.load_number]
            real_depot_arrival = None
            if not duration_match.empty:
                arr_time_str = duration_match.iloc[0]['ArriveAtDepot(Odo)']
                real_depot_arrival = parse_datetime_flexible(arr_time_str)
                if real_depot_arrival and real_depot_arrival != record.arrival_at_depot:
                    record.arrival_at_depot = real_depot_arrival
                    updated = True
            
            # Find real customer arrival time
            customer_match = customer_df[customer_df['load_name'] == record.load_number]
            real_customer_arrival = None
            if not customer_match.empty:
                cust_time_str = customer_match.iloc[0]['ArrivedAtCustomer(Odo)']
                real_customer_arrival = parse_datetime_flexible(cust_time_str)
                if real_customer_arrival and real_customer_arrival != record.arrival_at_customer:
                    record.arrival_at_customer = real_customer_arrival
                    updated = True
            
            # Only save if we found real timing data
            if updated:
                old_efficiency = record.efficiency_score
                record.save()  # This will recalculate total_time and efficiency_score
                updated_count += 1
                
                # Check if efficiency actually changed (meaning we had real timing data)
                if record.efficiency_score != old_efficiency and record.efficiency_score != 45.0:
                    efficiency_updated += 1
                
                if updated_count <= 20:  # Show first 20 updates
                    print(f"\n{record.load_number}:")
                    if real_departure:
                        print(f"  Real Departure: {real_departure}")
                    if real_depot_arrival:
                        print(f"  Real Depot Arrival: {real_depot_arrival}")
                    if real_customer_arrival:
                        print(f"  Real Customer Arrival: {real_customer_arrival}")
                    print(f"  Total Time: {record.total_time:.2f}h")
                    print(f"  Distance: {record.total_distance}km") 
                    print(f"  Efficiency: {record.efficiency_score:.1f} km/h")
                    
                    if record.efficiency_score != 45.0:
                        print(f"  ✓ REAL efficiency calculated!")
                    else:
                        print(f"  ⚠ Still using estimated efficiency")
        
        except Exception as e:
            if updated_count < 5:
                print(f"Error processing {record.load_number}: {e}")
            continue
    
    print(f"\n=== RESULTS ===")
    print(f"Updated {updated_count} records with real timing data")
    print(f"Records with non-45km/h efficiency: {efficiency_updated}")
    
    # Show some examples of records with real efficiency calculations
    print("\n=== RECORDS WITH REAL EFFICIENCY CALCULATIONS ===")
    real_efficiency_records = TruckPerformanceData.objects.exclude(
        efficiency_score__isnull=True
    ).exclude(efficiency_score=45.0)
    
    print(f"Found {real_efficiency_records.count()} records with variable efficiency")
    
    for record in real_efficiency_records[:10]:
        print(f"{record.load_number}: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h, {record.total_distance}km)")
    
    # Statistics
    print(f"\n=== FINAL STATISTICS ===")
    total = TruckPerformanceData.objects.count()
    with_efficiency = TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).count()
    variable_efficiency = TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).exclude(efficiency_score=45.0).count()
    
    print(f"Total records: {total}")
    print(f"Records with efficiency calculations: {with_efficiency}")
    print(f"Records with REAL (variable) efficiency: {variable_efficiency}")
    print(f"Records still using 45km/h estimate: {with_efficiency - variable_efficiency}")

if __name__ == "__main__":
    fix_efficiency_with_real_times()
