#!/usr/bin/env python
"""
Update Customer Names Script
Fixes Unknown Customer entries using data from uploaded CSV files
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

def update_customer_names():
    """Update Unknown Customer entries using available CSV data"""
    print("\n=== UPDATING CUSTOMER NAMES ===")
    print("-" * 30)
    
    # Get initial count of unknown customers
    unknown_before = TruckPerformanceData.objects.filter(customer_name='Unknown Customer').count()
    print(f"Unknown customers before update: {unknown_before}")
    
    # Get all customer timestamp files
    customer_files = CSVUpload.objects.filter(
        upload_type__in=['customer_timestamps', 'distance_info', 'time_routes']
    )
    
    updated_count = 0
    customer_mappings = {}
    
    # First pass: build customer mappings from all files
    for upload in customer_files:
        try:
            print(f"\nProcessing: {upload.file.name}")
            df = pd.read_csv(upload.file.path)
            
            # Try different possible column names for load and customer
            load_col = next((col for col in ['Load', 'Load Name', 'Load Number'] if col in df.columns), None)
            customer_col = next((col for col in ['Customer', 'customer_name', 'Customer Name'] if col in df.columns), None)
            
            if load_col and customer_col:
                for _, row in df.iterrows():
                    load_number = str(row[load_col]).strip()
                    customer_name = str(row[customer_col]).strip()
                    
                    if load_number and customer_name and customer_name != 'Unknown Customer':
                        customer_mappings[load_number] = customer_name
                        
        except Exception as e:
            print(f"Error reading {upload.file.name}: {str(e)}")
            continue
    
    # Second pass: update database records
    print("\nUpdating database records...")
    for load_number, customer_name in customer_mappings.items():
        try:
            updated = TruckPerformanceData.objects.filter(
                load_number=load_number,
                customer_name='Unknown Customer'
            ).update(customer_name=customer_name)
            
            if updated:
                updated_count += updated
                print(f"✓ Updated {load_number}: {customer_name}")
                
        except Exception as e:
            print(f"Error updating {load_number}: {str(e)}")
            continue
    
    # Get final count of unknown customers
    unknown_after = TruckPerformanceData.objects.filter(customer_name='Unknown Customer').count()
    
    print("\n=== UPDATE SUMMARY ===")
    print(f"Total records updated: {updated_count}")
    print(f"Unknown customers before: {unknown_before}")
    print(f"Unknown customers after: {unknown_after}")
    print(f"Improvement: {unknown_before - unknown_after} records fixed")
    
    if unknown_after > 0:
        print("\nRemaining unknown customers:")
        remaining_unknown = TruckPerformanceData.objects.filter(
            customer_name='Unknown Customer'
        ).values_list('load_number', flat=True)[:5]
        
        for load_number in remaining_unknown:
            print(f"- {load_number}")
        
        if unknown_after > 5:
            print(f"... and {unknown_after - 5} more")

if __name__ == "__main__":
    update_customer_names()
