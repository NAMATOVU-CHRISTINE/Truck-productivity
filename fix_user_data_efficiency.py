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
    
    formats = [
        '%m/%d/%y %H:%M',
        '%d/%m/%y %H:%M',  
        '%m/%d/%Y %H:%M',
        '%d/%m/%Y %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(str(date_str).strip(), fmt)
            return timezone.make_aware(dt, pytz.UTC)
        except ValueError:
            continue
    
    return None

def fix_efficiency_with_real_data():
    """Fix efficiency using the real timing data provided by user"""
    print("=== FIXING EFFICIENCY WITH REAL USER DATA ===")
    
    # Real timing data from user's export
    timing_data = [
        {'load': 'BM02L6QB', 'customer_arrival': '03/01/25 09:19', 'depot_arrival': '03/01/25 10:41'},
        {'load': 'BM02L6QT', 'customer_arrival': '04/01/25 12:08', 'depot_arrival': '04/01/25 13:42'},
        {'load': 'BM02L6QY', 'customer_arrival': '04/01/25 08:40', 'depot_arrival': '04/01/25 08:52'},
        {'load': 'BM02L6RG', 'customer_arrival': '12/31/24 09:35', 'depot_arrival': '01/01/25 14:58'},
        {'load': 'BM02L6RU', 'customer_arrival': '12/31/24 00:36', 'depot_arrival': '01/01/25 16:18'},
        {'load': 'BM02L6SN', 'customer_arrival': '12/31/24 06:09', 'depot_arrival': '01/01/25 18:00'},
        {'load': 'BM02L6SS', 'customer_arrival': '12/31/24 09:18', 'depot_arrival': '01/01/25 19:18'},
    ]
    
    print("BEFORE - Using estimated times (all showing 45.0 km/h):")
    for data in timing_data:
        try:
            record = TruckPerformanceData.objects.get(load_number=data['load'])
            print(f"{data['load']}: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h, {record.total_distance}km)")
        except TruckPerformanceData.DoesNotExist:
            print(f"{data['load']}: Not found")
    
    print("\n" + "="*60)
    print("UPDATING WITH REAL TIMING DATA...")
    
    updated_count = 0
    for data in timing_data:
        try:
            record = TruckPerformanceData.objects.get(load_number=data['load'])
            
            # Parse real timestamps
            real_customer_arrival = parse_datetime_flexible(data['customer_arrival'])
            real_depot_arrival = parse_datetime_flexible(data['depot_arrival'])
            
            if real_customer_arrival and real_depot_arrival:
                print(f"\n{data['load']}:")
                print(f"  Old depot arrival: {record.arrival_at_depot}")
                print(f"  Real customer arrival: {real_customer_arrival}")
                print(f"  Real depot arrival: {real_depot_arrival}")
                
                # Update with real timing data
                record.arrival_at_customer = real_customer_arrival
                record.arrival_at_depot = real_depot_arrival
                
                old_efficiency = record.efficiency_score
                record.save()  # This will recalculate total_time and efficiency_score
                updated_count += 1
                
                print(f"  OLD EFFICIENCY: {old_efficiency:.1f} km/h")
                print(f"  NEW EFFICIENCY: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h)")
                print(f"  Distance: {record.total_distance}km")
                
                if record.efficiency_score != 45.0:
                    print(f"  ✓ SUCCESS: Real efficiency calculated!")
                else:
                    print(f"  ⚠ Still showing 45km/h - may need departure time")
                
        except TruckPerformanceData.DoesNotExist:
            print(f"{data['load']}: Not found in database")
    
    print("\n" + "="*60)
    print("AFTER - Using real timing data:")
    for data in timing_data:
        try:
            record = TruckPerformanceData.objects.get(load_number=data['load'])
            efficiency_status = "✓ REAL" if record.efficiency_score != 45.0 else "⚠ ESTIMATED"
            print(f"{data['load']}: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h, {record.total_distance}km) {efficiency_status}")
        except TruckPerformanceData.DoesNotExist:
            print(f"{data['load']}: Not found")
    
    print(f"\nUpdated {updated_count} records with real timing data")
    
    # Show efficiency statistics
    print("\n=== EFFICIENCY STATISTICS ===")
    all_records = TruckPerformanceData.objects.exclude(efficiency_score__isnull=True)
    total_records = all_records.count()
    fixed_efficiency = all_records.exclude(efficiency_score=45.0).count()
    estimated_efficiency = all_records.filter(efficiency_score=45.0).count()
    
    print(f"Total records with efficiency: {total_records}")
    print(f"Records with REAL efficiency: {fixed_efficiency}")
    print(f"Records still using 45km/h estimate: {estimated_efficiency}")
    print(f"Percentage with real data: {(fixed_efficiency/total_records)*100:.1f}%")

if __name__ == "__main__":
    fix_efficiency_with_real_data()
