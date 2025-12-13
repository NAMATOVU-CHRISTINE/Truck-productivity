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
from dashboard.views import extract_unified_truck_data

def fix_timezone_issues(df):
    """Fix timezone-related issues in datetime columns"""
    datetime_columns = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['time', 'date', 'timestamp', 'arrival', 'departure']):
            datetime_columns.append(col)
    
    for col in datetime_columns:
        if col in df.columns:
            try:
                # Convert to string first to handle mixed types
                df[col] = df[col].astype(str)
                # Try to parse datetime
                df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
                # Remove timezone info to avoid Django issues
                df[col] = df[col].dt.tz_localize(None)
                print(f"Fixed timezone for column: {col}")
            except Exception as e:
                print(f"Could not fix timezone for {col}: {e}")
                # If all else fails, set to None
                df[col] = None
    
    return df

def process_customer_timestamps():
    """Process customer timestamps file with timezone fixes"""
    try:
        upload = CSVUpload.objects.get(upload_type='customer_timestamps', processed=False)
        print(f"Processing: {upload.file.name}")
        
        # Read the CSV
        df = pd.read_csv(upload.file.path)
        print(f"Original columns: {list(df.columns)}")
        print(f"Rows: {len(df)}")
        
        # Fix timezone issues
        df = fix_timezone_issues(df)
        
        # Process each row
        created_count = 0
        for index, row in df.iterrows():
            try:
                data = extract_unified_truck_data(row, 'customer_timestamps')
                if data.get('load_number'):
                    # Check for existing record to avoid duplicates
                    existing = TruckPerformanceData.objects.filter(
                        load_number=data['load_number']
                    ).first()
                    
                    if existing:
                        # Update existing record
                        for key, value in data.items():
                            if value is not None and value != '':
                                setattr(existing, key, value)
                        existing.save()
                        print(f"Updated existing record: {data['load_number']}")
                    else:
                        # Create new record
                        TruckPerformanceData.objects.create(**data)
                        created_count += 1
                        if created_count % 100 == 0:
                            print(f"Created {created_count} records...")
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        upload.processed = True
        upload.save()
        print(f"Customer timestamps processing completed. Created/updated records.")
        
    except Exception as e:
        print(f"Error processing customer timestamps: {e}")

def process_distance_info():
    """Process distance information file avoiding duplicates"""
    try:
        upload = CSVUpload.objects.get(upload_type='distance_info', processed=False)
        print(f"Processing: {upload.file.name}")
        
        # Read the CSV
        df = pd.read_csv(upload.file.path)
        print(f"Original columns: {list(df.columns)}")
        print(f"Rows: {len(df)}")
        
        # Process each row
        created_count = 0
        updated_count = 0
        
        for index, row in df.iterrows():
            try:
                data = extract_unified_truck_data(row, 'distance_info')
                if data.get('load_number'):
                    # Check for existing record
                    existing = TruckPerformanceData.objects.filter(
                        load_number=data['load_number']
                    ).first()
                    
                    if existing:
                        # Update existing record with distance data
                        updated = False
                        for key, value in data.items():
                            if value is not None and value != '' and key in ['d1', 'd2', 'd3', 'd4']:
                                current_value = getattr(existing, key)
                                if current_value is None or current_value == 0:
                                    setattr(existing, key, value)
                                    updated = True
                        
                        if updated:
                            existing.save()
                            updated_count += 1
                            if updated_count % 100 == 0:
                                print(f"Updated {updated_count} records with distance data...")
                    else:
                        # Create new record
                        TruckPerformanceData.objects.create(**data)
                        created_count += 1
                        if created_count % 100 == 0:
                            print(f"Created {created_count} records...")
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        upload.processed = True
        upload.save()
        print(f"Distance info processing completed. Created: {created_count}, Updated: {updated_count}")
        
    except Exception as e:
        print(f"Error processing distance info: {e}")

def main():
    print("Processing pending CSV files...")
    
    # Process customer timestamps
    try:
        process_customer_timestamps()
    except Exception as e:
        print(f"Failed to process customer timestamps: {e}")
    
    # Process distance information
    try:
        process_distance_info()
    except Exception as e:
        print(f"Failed to process distance info: {e}")
    
    # Show final stats
    total_records = TruckPerformanceData.objects.count()
    records_with_d1 = TruckPerformanceData.objects.exclude(d1__isnull=True).exclude(d1=0).count()
    records_with_d2 = TruckPerformanceData.objects.exclude(d2__isnull=True).exclude(d2=0).count()
    
    print(f"\nFinal Statistics:")
    print(f"Total records: {total_records}")
    print(f"Records with D1 data: {records_with_d1}")
    print(f"Records with D2 data: {records_with_d2}")
    
    # Show sample of recent data with distance values
    recent_with_data = TruckPerformanceData.objects.exclude(d1__isnull=True).exclude(d1=0)[:3]
    print(f"\nSample records with distance data:")
    for record in recent_with_data:
        print(f"Load: {record.load_number} | D1: {record.d1} | D2: {record.d2} | D3: {record.d3} | D4: {record.d4}")

if __name__ == "__main__":
    main()
