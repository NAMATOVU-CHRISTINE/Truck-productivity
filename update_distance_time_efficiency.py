#!/usr/bin/env python
"""
Update Distance, Time, and Efficiency Script
Fills in missing total_distance, total_time, and efficiency fields using uploaded CSV files
"""
import os
import django
import pandas as pd
from datetime import datetime
import pytz

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import CSVUpload, TruckPerformanceData
from django.utils import timezone

def update_distance_time_efficiency():
    """Update missing distance, time, and efficiency fields using available CSV data"""
    print("\n=== UPDATING DISTANCE, TIME, AND EFFICIENCY ===")
    print("-" * 40)
    
    # Get all relevant files
    distance_files = CSVUpload.objects.filter(upload_type__in=['distance_info', 'time_routes', 'time_in_route'])
    
    # Build mapping for distance and time
    distance_map = {}
    time_map = {}
    
    for upload in distance_files:
        try:
            print(f"\nProcessing: {upload.file.name}")
            df = pd.read_csv(upload.file.path)
            # Try to find columns for load, distance, and time
            load_col = next((col for col in ['Load', 'Load Name', 'Load Number'] if col in df.columns), None)
            dist_col = next((col for col in ['Total Distance', 'Distance', 'Total Distance (km)', 'Distance (km)'] if col in df.columns), None)
            time_col = next((col for col in ['Total Time', 'Time', 'Total Time (hrs)', 'Time (hrs)'] if col in df.columns), None)
            
            for _, row in df.iterrows():
                load_number = str(row[load_col]).strip() if load_col and row.get(load_col) else None
                distance = float(row[dist_col]) if dist_col and pd.notnull(row.get(dist_col)) else None
                time = float(row[time_col]) if time_col and pd.notnull(row.get(time_col)) else None
                if load_number:
                    if distance is not None:
                        distance_map[load_number] = distance
                    if time is not None:
                        time_map[load_number] = time
        except Exception as e:
            print(f"Error reading {upload.file.name}: {str(e)}")
            continue
    
    # Update database records
    print("\nUpdating database records...")
    updated_count = 0
    for load_number in set(list(distance_map.keys()) + list(time_map.keys())):
        try:
            record = TruckPerformanceData.objects.filter(load_number=load_number).first()
            if record:
                updated = False
                if load_number in distance_map and (record.total_distance is None or record.total_distance == 0):
                    record.total_distance = distance_map[load_number]
                    updated = True
                if load_number in time_map and (record.total_time is None or record.total_time == 0):
                    record.total_time = time_map[load_number]
                    updated = True
                # Calculate efficiency if both fields are present
                if record.total_distance and record.total_time and (record.efficiency is None or record.efficiency == 0):
                    try:
                        record.efficiency = round(record.total_distance / record.total_time, 2) if record.total_time > 0 else None
                        updated = True
                    except Exception:
                        pass
                if updated:
                    record.save()
                    updated_count += 1
                    print(f"✓ Updated {load_number}: distance={record.total_distance}, time={record.total_time}, efficiency={record.efficiency}")
        except Exception as e:
            print(f"Error updating {load_number}: {str(e)}")
            continue
    print(f"\n=== UPDATE SUMMARY ===\nTotal records updated: {updated_count}")

if __name__ == "__main__":
    update_distance_time_efficiency()
