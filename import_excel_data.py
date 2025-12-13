#!/usr/bin/env python
"""
Script to import truck productivity data from Excel file to Django database.
Run this script from the project root directory after setting up the Django environment.

Usage: python import_excel_data.py path/to/excel/file.xlsx
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime
from django.utils.dateparse import parse_datetime, parse_date

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import TruckPerformanceData, CSVUpload


def clean_datetime_string(dt_str):
    """Clean and parse datetime strings from Excel"""
    if pd.isna(dt_str) or dt_str == '' or dt_str is None:
        return None
    
    # Convert to string if it's not already
    dt_str = str(dt_str).strip()
    
    # Handle various datetime formats
    try:
        # Try parsing as Excel datetime first
        if isinstance(dt_str, str) and '/' in dt_str:
            # Format like "5/2/25 10:38"
            if len(dt_str.split('/')[2].split()[0]) == 2:  # 2-digit year
                dt_obj = datetime.strptime(dt_str, '%m/%d/%y %H:%M')
            else:  # 4-digit year
                dt_obj = datetime.strptime(dt_str, '%m/%d/%Y %H:%M')
            return dt_obj
        else:
            # Try other common formats
            return parse_datetime(dt_str)
    except (ValueError, AttributeError):
        return None


def clean_date_string(date_str):
    """Clean and parse date strings from Excel"""
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return None
    
    date_str = str(date_str).strip()
    
    try:
        # Handle date formats like "5/1/25 0:00"
        if ' 0:00' in date_str:
            date_str = date_str.replace(' 0:00', '')
        
        if '/' in date_str:
            if len(date_str.split('/')[2]) == 2:  # 2-digit year
                date_obj = datetime.strptime(date_str, '%m/%d/%y').date()
            else:  # 4-digit year
                date_obj = datetime.strptime(date_str, '%m/%d/%Y').date()
            return date_obj
        else:
            return parse_date(date_str)
    except (ValueError, AttributeError):
        return None


def clean_numeric_value(value):
    """Clean and convert numeric values"""
    if pd.isna(value) or value == '' or value is None:
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def clean_integer_value(value):
    """Clean and convert integer values"""
    if pd.isna(value) or value == '' or value is None:
        return None
    
    try:
        return int(float(value))  # Convert to float first to handle decimals, then to int
    except (ValueError, TypeError):
        return None


def import_excel_data(excel_file_path):
    """Import truck productivity data from Excel file"""
    
    print(f"Reading Excel file: {excel_file_path}")
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file_path)
        print(f"Found {len(df)} rows in Excel file")
        
        # Print column names to verify mapping
        print("Columns in Excel file:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")
        
        # Create a CSV upload record to track this import
        csv_upload = CSVUpload.objects.create(
            name=f"Excel Import - {os.path.basename(excel_file_path)}",
            upload_type='other',
            processed=True
        )
        
        successful_imports = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Create TruckPerformanceData object
                truck_data = TruckPerformanceData(
                    csv_upload=csv_upload,
                    
                    # Core fields
                    create_date=clean_date_string(row.get('Create Date')),
                    month_name=str(row.get('Month Name', '')).strip() if not pd.isna(row.get('Month Name')) else '',
                    transporter=str(row.get('Transporter', '')).strip() if not pd.isna(row.get('Transporter')) else '',
                    load_number=str(row.get('Load Number', '')).strip() if not pd.isna(row.get('Load Number')) else '',
                    mode_of_capture=str(row.get('Mode Of Capture', '')).strip() if not pd.isna(row.get('Mode Of Capture')) else '',
                    driver_name=str(row.get('Driver Name', '')).strip() if not pd.isna(row.get('Driver Name')) else '',
                    truck_number=str(row.get('Truck Number', '')).strip() if not pd.isna(row.get('Truck Number')) else '',
                    customer_name=str(row.get('Customer Name', '')).strip() if not pd.isna(row.get('Customer Name')) else '',
                    
                    # Timing fields
                    dj_departure_time=clean_datetime_string(row.get('DJ Departure Time')),
                    departure_deviation_min=clean_integer_value(row.get('Depature Deviation (min)')),  # Note: typo in original
                    ave_departure=clean_integer_value(row.get('AVE Departure')),
                    comment_ave_departure=str(row.get('Comment  AVE Departure', '')).strip() if not pd.isna(row.get('Comment  AVE Departure')) else '',
                    
                    # Customer service fields
                    arrival_at_customer=clean_datetime_string(row.get('Arrival At Customer')),
                    departure_time_from_customer=clean_datetime_string(row.get('Departure Time from Customer')),
                    service_time_at_customer=clean_integer_value(row.get('Service Time At Customer')),
                    comment_tat=str(row.get('Comment  TAT', '')).strip() if not pd.isna(row.get('Comment  TAT')) else '',
                    
                    # Depot return fields
                    arrival_at_depot=clean_datetime_string(row.get('Arrival At Depot')),
                    ave_arrival_time=clean_integer_value(row.get('AVE Arrival Time')),
                    
                    # Distance fields
                    d1=clean_numeric_value(row.get('D1')),
                    d2=clean_numeric_value(row.get('D2')),
                    d3=clean_numeric_value(row.get('D3')),
                    d4=clean_numeric_value(row.get('D4')),
                    
                    # Comments
                    comment_ave_tir=str(row.get('Comment Ave TIR', '')).strip() if not pd.isna(row.get('Comment Ave TIR')) else '',
                )
                
                # Validate required fields
                if not truck_data.create_date:
                    errors.append(f"Row {index + 2}: Missing create_date")
                    continue
                    
                if not truck_data.load_number:
                    errors.append(f"Row {index + 2}: Missing load_number")
                    continue
                
                # Save the object (this will trigger calculated field updates)
                truck_data.save()
                successful_imports += 1
                
                if successful_imports % 50 == 0:
                    print(f"Imported {successful_imports} records...")
                    
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                continue
        
        print(f"\nImport completed!")
        print(f"Successfully imported: {successful_imports} records")
        print(f"Errors encountered: {len(errors)}")
        
        if errors:
            print("\nFirst 10 errors:")
            for error in errors[:10]:
                print(f"  - {error}")
        
        return successful_imports, errors
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return 0, [str(e)]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python import_excel_data.py path/to/excel/file.xlsx")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        sys.exit(1)
    
    import_excel_data(file_path)
