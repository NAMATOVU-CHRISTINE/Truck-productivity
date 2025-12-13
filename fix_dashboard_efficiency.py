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
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y %H:%M:%S', 
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

def fix_dashboard_efficiency():
    """Fix efficiency for dashboard records using real arrival times"""
    print("=== FIXING DASHBOARD EFFICIENCY WITH REAL ARRIVAL TIMES ===")
    
    # Load the timestamps and duration CSV with real arrival times
    duration_df = pd.read_csv('media/uploads/4.Timestamps_and_Durat_1752480667772.csv')
    
    # Dashboard loads that user sees
    dashboard_loads = ['BM4HFKNRR', 'BMTXTLBRR', 'BMVFEJ0RR', 'BM9JV5NRR', 'BMP3QSPRR']
    
    print("BEFORE - Using estimated arrival times:")
    for load in dashboard_loads:
        try:
            record = TruckPerformanceData.objects.get(load_number=load)
            print(f"{load}: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h, {record.total_distance}km)")
            print(f"  Departure: {record.dj_departure_time}")  
            print(f"  Arrival (estimated): {record.arrival_at_depot}")
        except TruckPerformanceData.DoesNotExist:
            print(f"{load}: Not found")
    
    print("\n" + "="*50)
    print("UPDATING WITH REAL ARRIVAL TIMES...")
    
    for load in dashboard_loads:
        try:
            record = TruckPerformanceData.objects.get(load_number=load)
            
            # Find real arrival time from CSV
            csv_match = duration_df[duration_df['load_name'] == load]
            if not csv_match.empty:
                real_arrival_str = csv_match.iloc[0]['ArriveAtDepot(Odo)']
                real_arrival = parse_datetime_flexible(real_arrival_str)
                
                if real_arrival:
                    print(f"\n{load}:")
                    print(f"  Old arrival (estimated): {record.arrival_at_depot}")
                    print(f"  New arrival (real): {real_arrival}")
                    
                    # Update with real arrival time
                    record.arrival_at_depot = real_arrival
                    record.save()  # This will recalculate total_time and efficiency
                    
                    print(f"  NEW EFFICIENCY: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h)")
                    
        except TruckPerformanceData.DoesNotExist:
            print(f"{load}: Not found")
    
    print("\n" + "="*50)  
    print("AFTER - Using real arrival times:")
    for load in dashboard_loads:
        try:
            record = TruckPerformanceData.objects.get(load_number=load)
            print(f"{load}: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h, {record.total_distance}km)")
        except TruckPerformanceData.DoesNotExist:
            print(f"{load}: Not found")

if __name__ == "__main__":
    fix_dashboard_efficiency()
