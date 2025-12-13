#!/usr/bin/env python
import os
import django
import pandas as pd
from datetime import datetime, timedelta
import pytz
import sys
import traceback

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from django.utils import timezone
from dashboard.models import TruckPerformanceData

def safe_division(numerator, denominator):
    """Safely perform division, returning 0 if denominator is 0"""
    try:
        if denominator == 0:
            return 0
        return numerator / denominator
    except (ZeroDivisionError, TypeError):
        return 0

def safe_percentage(numerator, denominator):
    """Safely calculate percentage, returning 0.0 if denominator is 0"""
    try:
        if denominator == 0:
            return 0.0
        return (numerator / denominator) * 100
    except (ZeroDivisionError, TypeError):
        return 0.0

def safe_model_operation(operation, default_return=None, error_msg="Operation failed"):
    """Safely execute a model operation with error handling"""
    try:
        return operation()
    except Exception as e:
        print(f"  ⚠️  {error_msg}: {str(e)}")
        return default_return

def clean_and_enhance_system():
    """Clean data quality issues and enhance efficiency calculations - Error-Free Version"""
    
    print("="*60)
    print("TRUCK PRODUCTIVITY SYSTEM - CLEAN & ENHANCE (v2.0)")
    print("="*60)
    
    try:
        # 1. SYSTEM STATUS
        print("\n1. CURRENT SYSTEM STATUS")
        print("-" * 30)
        
        total = safe_model_operation(
            lambda: TruckPerformanceData.objects.count(),
            0,
            "Failed to count total records"
        )
        
        with_efficiency = safe_model_operation(
            lambda: TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).count(),
            0,
            "Failed to count efficiency records"
        )
        
        real_efficiency = safe_model_operation(
            lambda: TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).exclude(efficiency_score=45.0).count(),
            0,
            "Failed to count real efficiency records"
        )
        
        print(f"Total records: {total:,}")
        print(f"Records with efficiency: {with_efficiency:,}")
        
        if with_efficiency > 0:
            percentage = safe_percentage(real_efficiency, with_efficiency)
            print(f"Records with REAL efficiency: {real_efficiency:,} ({percentage:.1f}%)")
            print(f"Records with 45km/h estimate: {with_efficiency - real_efficiency:,}")
        else:
            print("Records with REAL efficiency: 0 (0.0%)")
            print("Records with 45km/h estimate: 0")
            print("\n🎯 DATABASE IS CLEAN - No data to debug!")
            print("="*60)
            print("SYSTEM READY FOR FRESH DATA UPLOAD")
            print("Start Django server: python manage.py runserver")
            print("Access dashboard: http://localhost:8000")
            print("="*60)
            return
        
        # 2. DATA QUALITY CLEANUP
        print("\n2. CLEANING DATA QUALITY ISSUES")
        print("-" * 35)
        
        # Fix negative time values
        negative_time_records = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(total_time__lt=0),
            TruckPerformanceData.objects.none(),
            "Failed to find negative time records"
        )
        
        count = safe_model_operation(lambda: negative_time_records.count(), 0)
        print(f"Found {count} records with negative time")
        
        fixed_negative = 0
        for record in negative_time_records:
            try:
                # Safely check if attributes exist before accessing
                if (hasattr(record, 'arrival_at_customer') and 
                    hasattr(record, 'arrival_at_depot') and
                    record.arrival_at_customer and 
                    record.arrival_at_depot and 
                    record.arrival_at_customer > record.arrival_at_depot):
                    
                    # Swap them - customer arrival should be before depot arrival
                    temp = record.arrival_at_customer
                    record.arrival_at_customer = record.arrival_at_depot
                    record.arrival_at_depot = temp
                    
                    safe_model_operation(
                        lambda: record.save(),
                        None,
                        f"Failed to save record {getattr(record, 'load_number', 'Unknown')}"
                    )
                    fixed_negative += 1

                    if fixed_negative <= 5:  # Show first 5 fixes
                        load_num = getattr(record, 'load_number', 'Unknown')
                        print(f"  Fixed {load_num}: swapped customer/depot arrivals")
                
            except Exception as e:
                if fixed_negative < 3:
                    load_num = getattr(record, 'load_number', 'Unknown')
                    print(f"  Error fixing {load_num}: {e}")
        
        print(f"Fixed {fixed_negative} negative time records")
        
        # Fix unrealistic efficiency values
        unrealistic_high = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(efficiency_score__gt=150),
            TruckPerformanceData.objects.none(),
            "Failed to find high efficiency records"
        )
        
        unrealistic_low = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(efficiency_score__lt=1, efficiency_score__gt=0),
            TruckPerformanceData.objects.none(),
            "Failed to find low efficiency records"
        )
        
        high_count = safe_model_operation(lambda: unrealistic_high.count(), 0)
        low_count = safe_model_operation(lambda: unrealistic_low.count(), 0)
        
        print(f"Found {high_count} records with >150 km/h efficiency")
        print(f"Found {low_count} records with <1 km/h efficiency")
        
        # Reset unrealistic values
        fixed_unrealistic = 0
        try:
            for record in list(unrealistic_high) + list(unrealistic_low):
                try:
                    record.efficiency_score = None
                    record.total_time = None
                    safe_model_operation(
                        lambda: record.save(),
                        None,
                        f"Failed to reset record {getattr(record, 'load_number', 'Unknown')}"
                    )
                    fixed_unrealistic += 1
                except Exception as e:
                    if fixed_unrealistic < 3:
                        load_num = getattr(record, 'load_number', 'Unknown')
                        print(f"  Error fixing {load_num}: {e}")
        except Exception as e:
            print(f"  Error processing unrealistic records: {e}")
        
        print(f"Reset {fixed_unrealistic} unrealistic efficiency values")
        
        # 3. ENHANCE EFFICIENCY CALCULATIONS
        print("\n3. ENHANCING EFFICIENCY CALCULATIONS")
        print("-" * 40)
        
        estimated_records = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(efficiency_score=45.0),
            TruckPerformanceData.objects.none(),
            "Failed to find estimated records"
        )
        
        est_count = safe_model_operation(lambda: estimated_records.count(), 0)
        print(f"Processing {est_count} records with estimated efficiency...")
        
        enhanced_count = 0
        try:
            for record in estimated_records[:100]:  # Process in batches
                try:
                    old_efficiency = getattr(record, 'efficiency_score', 45.0)
                    
                    # Safely check timing data
                    needs_update = False
                    
                    if (hasattr(record, 'dj_departure_time') and 
                        record.dj_departure_time and
                        hasattr(record.dj_departure_time, 'second')):
                        if (record.dj_departure_time.second != 0 and 
                            record.dj_departure_time.microsecond == 0):
                            needs_update = True
                    
                    if (hasattr(record, 'arrival_at_depot') and 
                        record.arrival_at_depot and
                        hasattr(record.arrival_at_depot, 'second')):
                        if (record.arrival_at_depot.second != 0 and
                            record.arrival_at_depot.microsecond == 0):
                            needs_update = True
                    
                    if needs_update:
                        safe_model_operation(
                            lambda: record.save(),
                            None,
                            f"Failed to enhance record {getattr(record, 'load_number', 'Unknown')}"
                        )
                        
                        new_efficiency = getattr(record, 'efficiency_score', old_efficiency)
                        if new_efficiency != old_efficiency:
                            enhanced_count += 1
                            
                            if enhanced_count <= 10:
                                load_num = getattr(record, 'load_number', 'Unknown')
                                print(f"  Enhanced {load_num}: {old_efficiency:.1f} → {new_efficiency:.1f} km/h")
                
                except Exception as e:
                    if enhanced_count < 3:
                        load_num = getattr(record, 'load_number', 'Unknown')
                        print(f"  Error enhancing {load_num}: {e}")
        except Exception as e:
            print(f"  Error processing estimated records: {e}")
        
        print(f"Enhanced {enhanced_count} efficiency calculations")
        
        # 4. IDENTIFY TOP PERFORMERS AND ISSUES
        print("\n4. PERFORMANCE ANALYSIS")
        print("-" * 25)
        
        # Best efficiency (but realistic)
        top_performers = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(
                efficiency_score__gte=60, efficiency_score__lte=100
            ).order_by('-efficiency_score')[:5],
            [],
            "Failed to find top performers"
        )
        
        print("TOP PERFORMING TRUCKS (60-100 km/h):")
        try:
            for record in top_performers:
                load_num = getattr(record, 'load_number', 'Unknown')
                efficiency = getattr(record, 'efficiency_score', 0)
                total_time = getattr(record, 'total_time', 0)
                distance = getattr(record, 'total_distance', 0)
                print(f"  {load_num}: {efficiency:.1f} km/h ({total_time:.1f}h, {distance}km)")
        except Exception as e:
            print(f"  Error displaying top performers: {e}")
        
        # Identify problematic records
        problem_records = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(
                efficiency_score__lt=10, efficiency_score__gt=0
            ).order_by('efficiency_score')[:5],
            [],
            "Failed to find problem records"
        )

        # print("\nPROBLEMATIC RECORDS (<10 km/h):")
        try:
            for record in problem_records:
                load_num = getattr(record, 'load_number', 'Unknown')
                efficiency = getattr(record, 'efficiency_score', 0)
                total_time = getattr(record, 'total_time', 0)
                distance = getattr(record, 'total_distance', 0)
                departure = getattr(record, 'dj_departure_time', 'N/A')
                arrival = getattr(record, 'arrival_at_depot', 'N/A')
                print(f"  {load_num}: {efficiency:.1f} km/h ({total_time:.1f}h, {distance}km)")
                print(f"    Departure: {departure}")
                print(f"    Arrival: {arrival}")
        except Exception as e:
            print(f"  Error displaying problem records: {e}")
        
        # 5. DASHBOARD STATUS CHECK
        print("\n5. DASHBOARD STATUS CHECK")
        print("-" * 30)
        
        dashboard_samples = safe_model_operation(
            lambda: TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).order_by('?')[:10],
            [],
            "Failed to get dashboard samples"
        )
        
        print("SAMPLE DASHBOARD RECORDS:")
        try:
            for record in dashboard_samples:
                load_num = getattr(record, 'load_number', 'Unknown')
                efficiency = getattr(record, 'efficiency_score', 0)
                total_time = getattr(record, 'total_time', 0)
                status = "✓ REAL" if efficiency != 45.0 else "⚠ ESTIMATED"
                print(f"  {load_num}: {efficiency:.1f} km/h ({total_time:.1f}h) {status}")
        except Exception as e:
            print(f"  Error displaying dashboard samples: {e}")
        
        # 6. FINAL SYSTEM STATUS
        print("\n6. UPDATED SYSTEM STATUS")
        print("-" * 30)
        
        # Refresh stats
        total = safe_model_operation(lambda: TruckPerformanceData.objects.count(), 0)
        with_efficiency = safe_model_operation(
            lambda: TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).count(), 0
        )
        real_efficiency = safe_model_operation(
            lambda: TruckPerformanceData.objects.exclude(efficiency_score__isnull=True).exclude(efficiency_score=45.0).count(), 0
        )
        
        print(f"Total records: {total:,}")
        print(f"Records with efficiency: {with_efficiency:,}")
        
        if with_efficiency > 0:
            percentage = safe_percentage(real_efficiency, with_efficiency)
            print(f"Records with REAL efficiency: {real_efficiency:,} ({percentage:.1f}%)")
            print(f"Records with 45km/h estimate: {with_efficiency - real_efficiency:,}")
        else:
            print("Records with REAL efficiency: 0 (0.0%)")
            print("Records with 45km/h estimate: 0")
        
        # Data quality after cleanup
        negative_time = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(total_time__lt=0).count(), 0
        )
        very_high_efficiency = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(efficiency_score__gt=150).count(), 0
        )
        very_low_efficiency = safe_model_operation(
            lambda: TruckPerformanceData.objects.filter(efficiency_score__lt=1, efficiency_score__gt=0).count(), 0
        )
        
        print(f"\nDATA QUALITY AFTER CLEANUP:")
        print(f"Records with negative time: {negative_time}")
        print(f"Records with >150 km/h efficiency: {very_high_efficiency}")
        print(f"Records with <1 km/h efficiency: {very_low_efficiency}")
        
        # 7. RECOMMENDATIONS
        print("\n7. RECOMMENDATIONS")
        print("-" * 20)
        
        if with_efficiency == 0:
            print("📝 CLEAN SYSTEM: Database is empty and ready for data upload")
            print("   → Upload CSV files through the web dashboard")
            print("   → Start with depot_departures, customer_timestamps, and distance_info files")
        else:
            efficiency_ratio = safe_division(real_efficiency, with_efficiency)
            if efficiency_ratio > 0.8:
                print("✓ EXCELLENT: >80% real efficiency data")
            elif efficiency_ratio > 0.6:
                print("✓ GOOD: >60% real efficiency data") 
            elif efficiency_ratio > 0.4:
                print("⚠ MODERATE: >40% real efficiency data - consider more CSV processing")
            else:
                print("❌ POOR: <40% real efficiency data - needs more timing data")
        
        if negative_time == 0 and very_high_efficiency == 0 and very_low_efficiency == 0:
            print("✓ CLEAN: No data quality issues detected")
        else:
            print("⚠ ISSUES: Some data quality problems remain - may need manual review")
        
        print("\n" + "="*60)
        print("CLEANUP AND ENHANCEMENT COMPLETE")
        print("="*60)
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR in main function: {e}")
        print("Stack trace:")
        traceback.print_exc()
        print("\n" + "="*60)
        print("SCRIPT TERMINATED DUE TO ERROR")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    try:
        clean_and_enhance_system()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
        print("\n" + "="*60)
        print("SCRIPT TERMINATED DUE TO UNEXPECTED ERROR")
        print("="*60)