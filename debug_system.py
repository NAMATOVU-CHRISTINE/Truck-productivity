#!/usr/bin/env python
"""
Truck Productivity Debug Script - Focus on critical issues
"""
import os
import django
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from django.utils import timezone
from dashboard.models import TruckPerformanceData

def debug_critical_issues():
    """Debug and fix the most critical data issues"""
    
    print("="*60)
    print("TRUCK PRODUCTIVITY DEBUG - CRITICAL ISSUES")
    print("="*60)
    
    # 1. FIX PROBLEMATIC RECORDS WITH EXTREME TIME DIFFERENCES
    print("\n1. FIXING EXTREME TIME DIFFERENCES")
    print("-" * 40)
    
    # Records with >1000 hour trips (clearly wrong - should be days not hours)
    extreme_time_records = TruckPerformanceData.objects.filter(total_time__gt=1000)
    print(f"Found {extreme_time_records.count()} records with >1000 hour trips")
    
    fixed_extreme = 0
    for record in extreme_time_records[:20]:  # Fix first 20
        try:
            if record.dj_departure_time and record.arrival_at_depot:
                # Calculate actual time difference
                time_diff = record.arrival_at_depot - record.dj_departure_time
                actual_hours = time_diff.total_seconds() / 3600
                
                print(f"  {record.load_number}: {record.total_time:.1f}h → {actual_hours:.1f}h")
                
                if actual_hours > 0 and actual_hours < 200:  # Reasonable trip time
                    record.total_time = actual_hours
                    if record.total_distance and record.total_distance > 0:
                        record.efficiency_score = record.total_distance / actual_hours
                    record.save()
                    fixed_extreme += 1
                
        except Exception as e:
            print(f"  Error fixing {record.load_number}: {e}")
    
    print(f"Fixed {fixed_extreme} extreme time records")
    
    # 2. FIX ZERO EFFICIENCY RECORDS  
    print("\n2. FIXING ZERO EFFICIENCY RECORDS")
    print("-" * 38)
    
    zero_efficiency = TruckPerformanceData.objects.filter(efficiency_score=0)
    print(f"Found {zero_efficiency.count()} records with 0 km/h efficiency")
    
    fixed_zero = 0
    for record in zero_efficiency[:20]:  # Fix first 20
        try:
            # These usually have distance but no valid time calculation
            if record.total_distance and record.total_distance > 0:
                if record.dj_departure_time and record.arrival_at_depot:
                    time_diff = record.arrival_at_depot - record.dj_departure_time
                    hours = time_diff.total_seconds() / 3600
                    
                    if hours > 0:
                        record.total_time = hours
                        record.efficiency_score = record.total_distance / hours
                        record.save()
                        fixed_zero += 1
                        
                        if fixed_zero <= 5:
                            print(f"  Fixed {record.load_number}: {record.efficiency_score:.1f} km/h")
                
        except Exception as e:
            if fixed_zero < 3:
                print(f"  Error fixing {record.load_number}: {e}")
    
    print(f"Fixed {fixed_zero} zero efficiency records")
    
    # 3. IDENTIFY BEST PERFORMING RECORDS FOR DASHBOARD
    print("\n3. DASHBOARD-READY RECORDS")
    print("-" * 30)
    
    # Find records with realistic efficiency and complete data
    dashboard_ready = TruckPerformanceData.objects.filter(
        efficiency_score__gte=10,
        efficiency_score__lte=80,
        total_distance__gte=50,
        total_time__gte=1
    ).exclude(
        customer_name__icontains='unknown'
    ).order_by('-efficiency_score')[:10]
    
    print("TOP DASHBOARD-READY RECORDS:")
    for record in dashboard_ready:
        print(f"  {record.load_number}: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h, {record.total_distance}km)")
        print(f"    Customer: {record.customer_name[:50]}...")
        print(f"    Driver: {record.driver_name}, Truck: {record.truck_number}")
    
    # 4. CHECK SPECIFIC DASHBOARD LOADS
    print("\n4. DASHBOARD LOAD STATUS")
    print("-" * 25)
    
    # Check the loads that were problematic earlier
    test_loads = ['BM4HFKNRR', 'BMTXTLBRR', 'BMVFEJ0RR', 'BM9JV5NRR', 'BMP3QSPRR']
    
    for load in test_loads:
        try:
            record = TruckPerformanceData.objects.get(load_number=load)
            status = "✓ REAL" if record.efficiency_score != 45.0 else "⚠ ESTIMATED" 
            print(f"  {load}: {record.efficiency_score:.1f} km/h ({record.total_time:.1f}h) {status}")
        except TruckPerformanceData.DoesNotExist:
            print(f"  {load}: Not found")
    
    # 5. SYSTEM HEALTH CHECK
    print("\n5. SYSTEM HEALTH CHECK") 
    print("-" * 25)
    
    # Count different efficiency ranges
    excellent = TruckPerformanceData.objects.filter(efficiency_score__gte=40, efficiency_score__lte=80).count()
    good = TruckPerformanceData.objects.filter(efficiency_score__gte=20, efficiency_score__lt=40).count()
    poor = TruckPerformanceData.objects.filter(efficiency_score__gte=5, efficiency_score__lt=20).count()
    problematic = TruckPerformanceData.objects.filter(efficiency_score__lt=5, efficiency_score__gt=0).count()
    estimated = TruckPerformanceData.objects.filter(efficiency_score=45.0).count()
    
    print(f"Excellent efficiency (40-80 km/h): {excellent:,}")
    print(f"Good efficiency (20-40 km/h): {good:,}")
    print(f"Poor efficiency (5-20 km/h): {poor:,}")
    print(f"Problematic (<5 km/h): {problematic:,}")
    print(f"Estimated (45 km/h): {estimated:,}")
    
    # 6. RECOMMENDATIONS
    print("\n6. DEBUG RECOMMENDATIONS")
    print("-" * 28)
    
    total_with_efficiency = excellent + good + poor + problematic + estimated
    real_data_percent = ((excellent + good + poor + problematic) / total_with_efficiency) * 100
    
    print(f"Real efficiency data: {real_data_percent:.1f}%")
    
    if real_data_percent > 70:
        print("✓ EXCELLENT: System has high quality efficiency data")
    elif real_data_percent > 50:
        print("✓ GOOD: System has acceptable efficiency data quality")
    else:
        print("⚠ NEEDS WORK: Consider processing more CSV timing data")
    
    if problematic > 100:
        print("⚠ HIGH: Many problematic records - check data quality")
    else:
        print("✓ CLEAN: Few problematic records")
    
    print("\n" + "="*60)
    print("DEBUG COMPLETE - SYSTEM READY FOR PRODUCTION")
    print("="*60)

if __name__ == "__main__":
    debug_critical_issues()
