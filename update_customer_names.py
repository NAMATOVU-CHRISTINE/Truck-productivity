#!/usr/bin/env python
import os
import sys
import django
import pandas as pd

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import TruckPerformanceData, CSVUpload

def update_customer_names():
    """Update customer names from files that contain customer information"""
    print("=== UPDATING CUSTOMER NAMES ===")
    
    # Files that contain customer information
    customer_files = [
        ('2.Customer_Timestamps__1752480054194.csv', 'customer_name'),
        ('3.Distance_Information_1752480636033.csv', 'Customer'),
        ('5.Time_in_Route_Inform_1752490636583.csv', 'Customer')
    ]
    
    update_count = 0
    
    for filename, customer_column in customer_files:
        file_path = f'media/uploads/{filename}'
        if os.path.exists(file_path):
            print(f"\\nProcessing customer data from: {filename}")
            
            try:
                # Read the CSV file
                df = pd.read_csv(file_path)
                print(f"Found {len(df)} rows in {filename}")
                
                # Get the load number column name (different in different files)
                load_column = None
                for col in df.columns:
                    if 'load' in col.lower() and ('name' in col.lower() or col.lower() == 'load'):
                        load_column = col
                        break
                
                if not load_column:
                    print(f"Could not find load column in {filename}")
                    continue
                    
                print(f"Using load column: {load_column}")
                print(f"Using customer column: {customer_column}")
                
                # Update records with customer names
                for _, row in df.iterrows():
                    load_number = str(row.get(load_column, '')).strip()
                    customer_name = str(row.get(customer_column, '')).strip()
                    
                    if load_number and customer_name and customer_name not in ['', 'nan', 'None']:
                        # Find matching records and update customer name
                        updated = TruckPerformanceData.objects.filter(
                            load_number=load_number,
                            customer_name='Unknown Customer'
                        ).update(customer_name=customer_name)
                        
                        if updated > 0:
                            update_count += updated
                            print(f"  Updated {updated} record(s) for load {load_number} with customer: {customer_name}")
                            
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
        else:
            print(f"File not found: {file_path}")
    
    print(f"\\n=== UPDATE COMPLETE ===")
    print(f"Total customer records updated: {update_count}")
    
    # Show sample of updated data
    print("\\nSample of updated data:")
    sample_records = TruckPerformanceData.objects.exclude(customer_name='Unknown Customer')[:10]
    for record in sample_records:
        print(f"  {record.load_number} | {record.driver_name} | {record.customer_name} | {record.truck_number}")

if __name__ == '__main__':
    update_customer_names()
