#!/usr/bin/env python
import os
import django
import pandas as pd
from datetime import datetime
import pytz

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import CSVUpload, TruckPerformanceData

def update_arrival_times():
    """Update arrival times from CSV files to calculate total_time and efficiency"""
    
    print("=== UPDATING ARRIVAL TIMES FOR TIME CALCULATIONS ===")
    
    # 1. Update arrival_at_customer from customer timestamps file
    print("\n1. Processing Customer Timestamps for arrival_at_customer...")
    customer_uploads = CSVUpload.objects.filter(upload_type='customer_timestamps')
    
    updated_customer = 0
    for upload in customer_uploads:
        print(f"Processing: {upload.file.name}")
        df = pd.read_csv(upload.file.path)
        
        for index, row in df.iterrows():
            load_number = str(row.get('load_name', ''))
            arrival_time = row.get('ArrivedAtCustomer(Odo)', '')
            
            if load_number and arrival_time and arrival_time != 'NaN' and pd.notna(arrival_time):
                try:
                    # Parse the arrival time
                    arrival_datetime = pd.to_datetime(arrival_time, errors='coerce')
                    if pd.notna(arrival_datetime):
                        # Remove timezone info to avoid Django issues
                        if arrival_datetime.tz is not None:
                            arrival_datetime = arrival_datetime.tz_localize(None)
                        
                        # Update the record
                        records = TruckPerformanceData.objects.filter(load_number=load_number)
                        for record in records:
                            record.arrival_at_customer = arrival_datetime
                            record.save()  # This will trigger recalculation
                            updated_customer += 1
                            if updated_customer <= 5:  # Show first 5 updates
                                print(f"  Updated {load_number}: arrival_at_customer = {arrival_datetime}")
                except Exception as e:
                    if index < 5:  # Only show first 5 errors
                        print(f"  Error processing {load_number}: {e}")
    
    print(f"Updated arrival_at_customer for {updated_customer} records")
    
    # 2. Update arrival_at_depot from timestamps duration file
    print("\n2. Processing Timestamps Duration for arrival_at_depot...")
    depot_uploads = CSVUpload.objects.filter(upload_type='timestamps_duration')
    
    updated_depot = 0
    for upload in depot_uploads:
        print(f"Processing: {upload.file.name}")
        df = pd.read_csv(upload.file.path)
        
        for index, row in df.iterrows():
            load_number = str(row.get('load_name', ''))
            arrival_time = row.get('ArriveAtDepot(Odo)', '')
            
            if load_number and arrival_time and arrival_time != 'NaN' and pd.notna(arrival_time):
                try:
                    # Parse the arrival time
                    arrival_datetime = pd.to_datetime(arrival_time, errors='coerce')
                    if pd.notna(arrival_datetime):
                        # Remove timezone info
                        if arrival_datetime.tz is not None:
                            arrival_datetime = arrival_datetime.tz_localize(None)
                        
                        # Update the record
                        records = TruckPerformanceData.objects.filter(load_number=load_number)
                        for record in records:
                            record.arrival_at_depot = arrival_datetime
                            record.save()  # This will trigger recalculation
                            updated_depot += 1
                            if updated_depot <= 5:  # Show first 5 updates
                                print(f"  Updated {load_number}: arrival_at_depot = {arrival_datetime}")
                except Exception as e:
                    if index < 5:  # Only show first 5 errors
                        print(f"  Error processing {load_number}: {e}")
    
    print(f"Updated arrival_at_depot for {updated_depot} records")
    
    # 3. Show results for test loads
    print("\n3. Checking results for sample loads...")
    test_loads = ['BM4HFKNRR', 'BMTXTLBRR', 'BMVFEJ0RR']
    for load in test_loads:
        try:
            record = TruckPerformanceData.objects.get(load_number=load)
            print(f"\n{load}:")
            print(f"  Departure: {record.dj_departure_time}")
            print(f"  Arrival Customer: {record.arrival_at_customer}")
            print(f"  Arrival Depot: {record.arrival_at_depot}")
            print(f"  Total Time: {record.total_time} hours")
            print(f"  Total Distance: {record.total_distance} km")
            print(f"  Efficiency: {record.efficiency_score} km/h")
        except Exception as e:
            print(f"Error checking {load}: {e}")
    
    # 4. Overall statistics
    print("\n4. Final Statistics...")
    total_records = TruckPerformanceData.objects.count()
    records_with_time = TruckPerformanceData.objects.exclude(total_time__isnull=True).count()
    records_with_efficiency = TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).count()
    
    print(f"Total records: {total_records}")
    print(f"Records with total_time: {records_with_time}")
    print(f"Records with efficiency_score: {records_with_efficiency}")
    
    print("\n=== ARRIVAL TIME UPDATE COMPLETE ===")

if __name__ == "__main__":
    update_arrival_times()
