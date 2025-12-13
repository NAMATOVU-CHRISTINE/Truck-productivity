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

def process_all_files_of_type(upload_type):
    """Process ALL files of a specific type (not just pending ones)"""
    try:
        # Get ALL files of this type, not just pending ones
        uploads = CSVUpload.objects.filter(upload_type=upload_type)
        
        if not uploads.exists():
            print(f"No files found for type: {upload_type}")
            return
            
        print(f"\n=== Processing ALL {upload_type} files ({uploads.count()} files) ===")
        
        total_created = 0
        total_updated = 0
        
        for upload in uploads:
            print(f"\nProcessing: {upload.file.name}")
            
            try:
                # Read the CSV
                df = pd.read_csv(upload.file.path)
                print(f"  Columns: {len(df.columns)}, Rows: {len(df)}")
                
                # Fix timezone issues for customer_timestamps
                if upload_type == 'customer_timestamps':
                    df = fix_timezone_issues(df)
                
                # Process each row
                file_created = 0
                file_updated = 0
                
                for index, row in df.iterrows():
                    try:
                        data = extract_unified_truck_data(row, upload_type)
                        if data.get('load_number'):
                            # Check for existing record
                            existing = TruckPerformanceData.objects.filter(
                                load_number=data['load_number']
                            ).first()
                            
                            if existing:
                                # Update existing record
                                updated = False
                                for key, value in data.items():
                                    if value is not None and value != '':
                                        # For distance fields, only update if current value is None or 0
                                        if key in ['d1', 'd2', 'd3', 'd4']:
                                            current_value = getattr(existing, key)
                                            if current_value is None or current_value == 0:
                                                setattr(existing, key, value)
                                                updated = True
                                        else:
                                            setattr(existing, key, value)
                                            updated = True
                                
                                if updated:
                                    existing.save()
                                    file_updated += 1
                                    total_updated += 1
                            else:
                                # Create new record
                                TruckPerformanceData.objects.create(**data)
                                file_created += 1
                                total_created += 1
                                
                    except Exception as e:
                        if index < 5:  # Only show first 5 errors per file
                            print(f"    Error processing row {index}: {e}")
                        continue
                
                print(f"  Results: Created {file_created}, Updated {file_updated}")
                
                # Mark as processed
                upload.processed = True
                upload.save()
                
            except Exception as e:
                print(f"  Error processing file {upload.file.name}: {e}")
                continue
        
        print(f"\n=== {upload_type} COMPLETE ===")
        print(f"Total Created: {total_created}")
        print(f"Total Updated: {total_updated}")
        
    except Exception as e:
        print(f"Error processing {upload_type} files: {e}")

def main():
    print("=== PROCESSING ALL CSV FILES ===")
    print("This will process ALL uploaded CSV files, regardless of processed status.")
    
    # Define all file types
    file_types = [
        'depot_departures',
        'customer_timestamps', 
        'distance_info',
        'timestamps_duration',
        'route_time',
        'drive_behavior'
    ]
    
    # Process each file type
    for file_type in file_types:
        process_all_files_of_type(file_type)
    
    # Show final comprehensive stats
    print("\n" + "="*60)
    print("FINAL COMPREHENSIVE STATISTICS")
    print("="*60)
    
    total_records = TruckPerformanceData.objects.count()
    print(f"Total records in database: {total_records}")
    
    # Count records with various data
    records_with_d1 = TruckPerformanceData.objects.exclude(d1__isnull=True).exclude(d1=0).count()
    records_with_d2 = TruckPerformanceData.objects.exclude(d2__isnull=True).exclude(d2=0).count()
    records_with_d3 = TruckPerformanceData.objects.exclude(d3__isnull=True).exclude(d3=0).count()
    records_with_d4 = TruckPerformanceData.objects.exclude(d4__isnull=True).exclude(d4=0).count()
    
    real_customers = TruckPerformanceData.objects.exclude(customer_name='Unknown Customer').count()
    
    print(f"Records with D1 data: {records_with_d1}")
    print(f"Records with D2 data: {records_with_d2}")
    print(f"Records with D3 data: {records_with_d3}")
    print(f"Records with D4 data: {records_with_d4}")
    print(f"Records with real customer names: {real_customers}")
    
    # Show sample of complete records
    complete_records = TruckPerformanceData.objects.exclude(
        d1__isnull=True
    ).exclude(
        customer_name='Unknown Customer'
    )[:5]
    
    print(f"\nSample complete records:")
    for record in complete_records:
        print(f"  {record.load_number} | {record.driver_name} | {record.customer_name[:30]}... | D1:{record.d1} D2:{record.d2}")
    
    print("\n=== PROCESSING COMPLETE ===")

if __name__ == "__main__":
    main()
