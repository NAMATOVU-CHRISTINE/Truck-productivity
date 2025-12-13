#!/usr/bin/env python
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import CSVUpload, TruckPerformanceData
from django.core.files import File
import pandas as pd
from datetime import datetime

def process_fixed_files():
    """Process files with correct field mapping based on actual CSV structure"""
    
    # Clear existing data first
    print("Clearing existing data...")
    TruckPerformanceData.objects.all().delete()
    
    processed_count = 0
    
    # Process each file type with correct field mappings
    files_to_process = [
        ('1.Depot_Departures_Inf_1752480585396.csv', 'depot_departures'),
        ('2.Customer_Timestamps__1752480054194.csv', 'customer_timestamps'),
        ('3.Distance_Information_1752480636033.csv', 'distance_info'),
        ('4.Timestamps_and_Durat_1752480667772.csv', 'timestamps_duration'),
        ('5.Average_Time_In_Rout_1752480705868.csv', 'avg_time_route'),
        ('6.Time_in_Route_Inform_1752490636583.csv', 'time_route_info')
    ]
    
    for filename, file_type in files_to_process:
        file_path = f"C:\\Users\\CHRISTINE\\OneDrive\\Desktop\\Fix\\media\\uploads\\{filename}"
        
        if os.path.exists(file_path):
            print(f"\\nProcessing {filename} as {file_type}")
            
            try:
                # Get or create CSVUpload record
                csv_upload = CSVUpload.objects.filter(name=filename).first()
                if not csv_upload:
                    print(f"No CSVUpload record found for {filename}")
                    continue
                
                # Read CSV
                df = pd.read_csv(file_path)
                print(f"Read {len(df)} rows")
                
                # Process based on type with correct field mappings
                if file_type == 'depot_departures':
                    success = process_depot_departures_fixed(df, csv_upload)
                elif file_type == 'customer_timestamps':
                    success = process_customer_timestamps_fixed(df, csv_upload)
                elif file_type == 'distance_info':
                    success = process_distance_info_fixed(df, csv_upload)
                elif file_type == 'timestamps_duration':
                    success = process_timestamps_duration_fixed(df, csv_upload)
                elif file_type == 'avg_time_route':
                    success = process_avg_time_route_fixed(df, csv_upload)
                elif file_type == 'time_route_info':
                    success = process_time_route_info_fixed(df, csv_upload)
                else:
                    success = False
                
                if success:
                    processed_count += 1
                    print(f"✅ Successfully processed {filename}")
                else:
                    print(f"❌ Failed to process {filename}")
                    
            except Exception as e:
                print(f"❌ Error processing {filename}: {str(e)}")
    
    print(f"\\n🎉 Processing complete! Successfully processed {processed_count} files.")
    
    # Show final counts
    total_uploads = CSVUpload.objects.count()
    total_records = TruckPerformanceData.objects.count()
    print(f"📊 Total CSVUpload records: {total_uploads}")
    print(f"📊 Total TruckPerformanceData records: {total_records}")
    
    if total_records > 0:
        print("\\n✨ Your data is ready! You can now download the combined Excel report.")

def safe_date_parse(date_str):
    """Safely parse date strings"""
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return datetime.now().date()
    
    try:
        return pd.to_datetime(date_str).date()
    except:
        return datetime.now().date()

def safe_time_parse(time_str):
    """Safely parse time strings"""
    if pd.isna(time_str) or time_str == '' or time_str is None:
        return None
    
    try:
        return pd.to_datetime(time_str).time()
    except:
        return None

def process_depot_departures_fixed(df, csv_upload):
    """Process depot departures with actual column names"""
    try:
        count = 0
        for index, row in df.iterrows():
            # Use actual column names from your CSV
            create_date = safe_date_parse(row.get('Schedule Date'))
            
            data = {
                'csv_upload': csv_upload,
                'create_date': create_date,
                'month_name': create_date.strftime('%B'),
                'transporter': str(row.get('Depot', 'Unknown')),
                'load_number': str(row.get('Load Name', f'LOAD_{index}')),
                'mode_of_capture': str(row.get('Hired/Own', 'Manual')),
                'driver_name': str(row.get('Driver Name', 'Unknown')),
                'truck_number': str(row.get('Vehicle Reg', 'Unknown')),
                'customer_name': 'Unknown',  # Not in this file
                'dj_departure_time': safe_time_parse(row.get('DJ Departure Time')),
            }
            
            TruckPerformanceData.objects.update_or_create(
                csv_upload=csv_upload,
                load_number=data['load_number'],
                defaults=data
            )
            count += 1
            
        print(f"   Created {count} records from depot departures")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def process_customer_timestamps_fixed(df, csv_upload):
    """Process customer timestamps with actual column names"""
    try:
        count = 0
        for index, row in df.iterrows():
            create_date = safe_date_parse(row.get('schedule_date'))
            
            # Update existing records or create new ones
            load_number = str(row.get('load_name', f'LOAD_{index}'))
            
            # Try to find existing record first
            existing_record = TruckPerformanceData.objects.filter(
                load_number=load_number
            ).first()
            
            if existing_record:
                # Update existing record
                existing_record.customer_name = str(row.get('customer_name', existing_record.customer_name or 'Unknown'))
                existing_record.driver_name = str(row.get('DriverName', existing_record.driver_name or 'Unknown'))
                existing_record.save()
            else:
                # Create new record
                data = {
                    'csv_upload': csv_upload,
                    'create_date': create_date,
                    'month_name': create_date.strftime('%B'),
                    'load_number': load_number,
                    'customer_name': str(row.get('customer_name', 'Unknown')),
                    'driver_name': str(row.get('DriverName', 'Unknown')),
                    'transporter': str(row.get('Depot', 'Unknown')),
                    'mode_of_capture': 'Manual',
                    'truck_number': 'Unknown',
                }
                
                TruckPerformanceData.objects.create(**data)
            
            count += 1
            
        print(f"   Updated {count} records with customer data")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def process_distance_info_fixed(df, csv_upload):
    """Process distance information with actual column names"""
    try:
        count = 0
        for index, row in df.iterrows():
            load_number = str(row.get('Load Name', f'LOAD_{index}'))
            
            # Try to find existing record first
            existing_record = TruckPerformanceData.objects.filter(
                load_number=load_number
            ).first()
            
            if existing_record:
                # Update with distance info
                existing_record.d1 = str(row.get('PlannedDistanceToCustomer', ''))
                existing_record.d2 = str(row.get('Total DJ Distance for Load', ''))
                existing_record.d3 = str(row.get('Distance Difference (Planned vs DJ)', ''))
                existing_record.d4 = str(row.get('Load Distance Difference (Planned vs. DJ)', ''))
                existing_record.save()
            else:
                # Create new record
                create_date = safe_date_parse(row.get('Schedule Date'))
                data = {
                    'csv_upload': csv_upload,
                    'create_date': create_date,
                    'month_name': create_date.strftime('%B'),
                    'load_number': load_number,
                    'driver_name': str(row.get('Driver Name', 'Unknown')),
                    'truck_number': str(row.get('Vehicle Reg', 'Unknown')),
                    'customer_name': str(row.get('Customer', 'Unknown')),
                    'transporter': str(row.get('Depot', 'Unknown')),
                    'mode_of_capture': str(row.get('Hired/Own', 'Manual')),
                    'd1': str(row.get('PlannedDistanceToCustomer', '')),
                    'd2': str(row.get('Total DJ Distance for Load', '')),
                    'd3': str(row.get('Distance Difference (Planned vs DJ)', '')),
                    'd4': str(row.get('Load Distance Difference (Planned vs. DJ)', '')),
                }
                
                TruckPerformanceData.objects.create(**data)
            
            count += 1
            
        print(f"   Updated {count} records with distance data")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def process_timestamps_duration_fixed(df, csv_upload):
    """Process timestamps and duration with actual column names"""
    try:
        count = 0
        for index, row in df.iterrows():
            load_number = str(row.get('load_name', f'LOAD_{index}'))
            
            # Try to find existing record first
            existing_record = TruckPerformanceData.objects.filter(
                load_number=load_number
            ).first()
            
            if existing_record:
                # Update with timestamp info
                existing_record.arrival_at_depot = safe_time_parse(row.get('ArriveAtDepot(Odo)'))
                existing_record.save()
            else:
                # Create new record
                create_date = safe_date_parse(row.get('schedule_date'))
                data = {
                    'csv_upload': csv_upload,
                    'create_date': create_date,
                    'month_name': create_date.strftime('%B'),
                    'load_number': load_number,
                    'transporter': str(row.get('Depot', 'Unknown')),
                    'mode_of_capture': 'Manual',
                    'driver_name': 'Unknown',
                    'truck_number': 'Unknown',
                    'customer_name': 'Unknown',
                    'arrival_at_depot': safe_time_parse(row.get('ArriveAtDepot(Odo)')),
                }
                
                TruckPerformanceData.objects.create(**data)
            
            count += 1
            
        print(f"   Updated {count} records with timestamp data")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def process_avg_time_route_fixed(df, csv_upload):
    """Process average time in route with actual column names"""
    try:
        count = 0
        for index, row in df.iterrows():
            customer_name = str(row.get('customer_name', 'Unknown'))
            avg_time_diff = str(row.get('Time In Route Difference ( DJ - Planned) (AVG)', ''))
            
            # Update all records with this customer
            updated = TruckPerformanceData.objects.filter(
                customer_name=customer_name
            ).update(
                comment_ave_tir=avg_time_diff
            )
            
            if updated == 0:
                # Create a summary record
                data = {
                    'csv_upload': csv_upload,
                    'create_date': datetime.now().date(),
                    'month_name': datetime.now().strftime('%B'),
                    'load_number': f'AVG_{index}',
                    'customer_name': customer_name,
                    'comment_ave_tir': avg_time_diff,
                    'transporter': 'Unknown',
                    'mode_of_capture': 'Manual',
                    'driver_name': 'Unknown',
                    'truck_number': 'Unknown',
                }
                
                TruckPerformanceData.objects.create(**data)
            
            count += 1
            
        print(f"   Updated {count} customer average records")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def process_time_route_info_fixed(df, csv_upload):
    """Process time in route information with actual column names"""
    try:
        count = 0
        for index, row in df.iterrows():
            load_number = str(row.get('Load', f'LOAD_{index}'))
            
            # Try to find existing record first
            existing_record = TruckPerformanceData.objects.filter(
                load_number=load_number
            ).first()
            
            if existing_record:
                # Update with route time info
                existing_record.ave_arrival_time = safe_time_parse(row.get('Time in Route (min)'))
                existing_record.save()
            else:
                # Create new record
                create_date = safe_date_parse(row.get('Schedule Date'))
                data = {
                    'csv_upload': csv_upload,
                    'create_date': create_date,
                    'month_name': create_date.strftime('%B'),
                    'load_number': load_number,
                    'driver_name': str(row.get('Driver', 'Unknown')),
                    'customer_name': str(row.get('Customer', 'Unknown')),
                    'transporter': str(row.get('Depot Code', 'Unknown')),
                    'mode_of_capture': 'Manual',
                    'truck_number': 'Unknown',
                    'ave_arrival_time': safe_time_parse(row.get('Time in Route (min)')),
                }
                
                TruckPerformanceData.objects.create(**data)
            
            count += 1
            
        print(f"   Updated {count} records with route time data")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    process_fixed_files()
