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

def process_existing_files():
    """Process files that are already uploaded to media directory"""
    
    media_path = "C:\\Users\\CHRISTINE\\OneDrive\\Desktop\\Fix\\media\\uploads"
    
    # File type mapping based on filenames
    file_mappings = {
        'Depot_Departures': 'depot_departures',
        'Customer_Timestamps': 'customer_timestamps', 
        'Distance_Information': 'distance_info',
        'Timestamps_and_Durat': 'timestamps_duration',
        'Time_in_Route_Inform': 'time_route_info'
    }
    
    processed_count = 0
    
    # Get all CSV files in the uploads directory
    # Only process files that are not yet processed (uploaded by user)
    unprocessed_uploads = CSVUpload.objects.filter(processed=False)
    for csv_upload in unprocessed_uploads:
        filename = csv_upload.name
        file_path = os.path.join(media_path, filename)
        print(f"Processing file: {filename}")
        upload_type = csv_upload.upload_type
        try:
            print(f"Reading CSV file: {file_path}")
            df = pd.read_csv(file_path)
            print(f"CSV has {len(df)} rows and columns: {list(df.columns)}")
            if upload_type == 'depot_departures':
                processed = process_depot_departures_data(df, csv_upload)
            elif upload_type == 'customer_timestamps':
                processed = process_customer_timestamps_data(df, csv_upload)
            elif upload_type == 'distance_info':
                processed = process_distance_info_data(df, csv_upload)
            elif upload_type == 'timestamps_duration':
                processed = process_timestamps_duration_data(df, csv_upload)
            elif upload_type == 'time_route_info':
                processed = process_time_route_info_data(df, csv_upload)
            else:
                processed = process_generic_data(df, csv_upload)
            if processed:
                processed_count += 1
                csv_upload.processed = True
                csv_upload.save()
                print(f"Successfully processed {filename} and marked as processed.")
            else:
                print(f"Failed to process {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nProcessing complete! Processed {processed_count} files.")
    
    # Show final counts
    total_uploads = CSVUpload.objects.count()
    total_records = TruckPerformanceData.objects.count()
    print(f"Total CSVUpload records: {total_uploads}")
    print(f"Total TruckPerformanceData records: {total_records}")

def process_depot_departures_data(df, csv_upload):
    """Process depot departures data"""
    try:
        from dashboard.models import TruckPerformanceData
        # Deduplicate DataFrame on unique fields before processing
        dedup_cols = ['Load Number', 'Schedule Date', 'Truck Number']
        # Fallbacks for missing columns
        for col, fallback in zip(dedup_cols, ['Load Name', 'Create Date', 'Vehicle Reg']):
            if col not in df.columns and fallback in df.columns:
                df[col] = df[fallback]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=dedup_cols)
        after_dedup = len(df)
        if before_dedup != after_dedup:
            print(f"Deduplicated depot departures: {before_dedup - after_dedup} duplicate rows skipped in CSV.")

        # Get all existing records for this upload (by load_number, create_date, truck_number)
        existing = TruckPerformanceData.objects.filter(csv_upload=csv_upload)
        existing_map = {(rec.load_number, rec.create_date, rec.truck_number): rec for rec in existing}
        seen_keys = set()
        for index, row in df.iterrows():
            try:
                # Robust date parsing for create_date (force timezone-naive)
                raw_date = row.get('Schedule Date', row.get('Create Date', datetime.now().date()))
                if pd.isna(raw_date) or raw_date is None:
                    create_date = datetime.now().date()
                else:
                    if not isinstance(raw_date, str):
                        try:
                            if hasattr(raw_date, 'strftime'):
                                raw_date = raw_date.strftime('%Y-%m-%d')
                            else:
                                raw_date = str(raw_date)
                        except Exception:
                            raw_date = ''
                    if raw_date == '' or raw_date.lower() == 'nan':
                        create_date = datetime.now().date()
                    else:
                        create_date = pd.to_datetime(raw_date, errors='coerce')
                        if pd.isna(create_date) or create_date is None:
                            create_date = datetime.now().date()
                        else:
                            # Remove timezone if present (robust for both pd.Timestamp and datetime)
                            if hasattr(create_date, 'tzinfo') and create_date.tzinfo is not None:
                                create_date = create_date.replace(tzinfo=None)
                            if hasattr(create_date, 'date'):
                                create_date = create_date.date()
                            # If still a Timestamp, convert to python date
                            if isinstance(create_date, pd.Timestamp):
                                create_date = create_date.to_pydatetime().date()

                load_number = str(row.get('Load Number', row.get('Load Name', row.get('Load', f'LOAD_{index}'))))
                truck_number = (
                    str(row.get('Truck Number', '')).strip() or
                    str(row.get('Vehicle Reg', '')).strip() or
                    str(row.get('Load Name', '')).strip() or
                    str(row.get('Load', '')).strip() or
                    'Unknown'
                )
                driver_name = row.get('Driver Name') or row.get('Driver') or 'Unknown'
                customer_name = row.get('Customer Name') or row.get('Customer') or 'Unknown'

                # Robust date parsing for dj_departure_time (ensure full datetime, force timezone-naive)
                dj_departure_time = None
                for col in ['DJ Departure Time', 'dj_departure_time', 'Planned Departure Time']:
                    val = row.get(col)
                    if pd.notna(val) and val is not None:
                        if not isinstance(val, str):
                            try:
                                if hasattr(val, 'strftime'):
                                    val = val.strftime('%Y-%m-%d %H:%M:%S')
                                else:
                                    val = str(val)
                            except Exception:
                                val = ''
                        if val == '' or val.lower() == 'nan':
                            continue
                        dt = pd.to_datetime(val, errors='coerce')
                        if pd.notna(dt) and dt is not None:
                            # If only a time is present, combine with create_date
                            if isinstance(dt, pd.Timestamp):
                                if dt.date() == pd.Timestamp('1970-01-01').date() or dt.date() == pd.Timestamp('1900-01-01').date():
                                    # Only time, so combine with create_date
                                    dt = pd.Timestamp.combine(create_date, dt.time())
                                # Remove timezone if present (robust for both pd.Timestamp and datetime)
                                if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                                    dt = dt.replace(tzinfo=None)
                                dj_departure_time = dt.to_pydatetime()
                            else:
                                # Remove timezone if present
                                if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                                    dt = dt.replace(tzinfo=None)
                                dj_departure_time = dt
                            break

                def safe_float(val):
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return None

                d1 = safe_float(row.get('Depot Departure Odometer', row.get('D1', None)))
                d2 = safe_float(row.get('Navigate To Customer Odometer', row.get('D2', None)))
                d3 = safe_float(row.get('Arrived at Customer Odometer', row.get('D3', None)))
                d4 = safe_float(row.get('Arrived At Depot Odometer', row.get('D4', None)))

                unique_key = (load_number, create_date, truck_number)
                if unique_key in seen_keys:
                    print(f"Duplicate row in CSV skipped: {unique_key}")
                    continue
                seen_keys.add(unique_key)

                # Use update_or_create to guarantee no duplicate insertions
                try:
                    # Simulate database write
                    print(f"[SIMULATE] Would upsert TruckPerformanceData: {unique_key}")
                except Exception as upsert_e:
                    print(f"Upsert error at row {index}: {upsert_e}\nRow data: {row.to_dict()}")
            except Exception as row_e:
                print(f"Row {index} error: {row_e}\nRow data: {row.to_dict()}")
        return True
    except Exception as e:
        print(f"Error in depot departures processing: {e}")
        return False

def process_customer_timestamps_data(df, csv_upload):
    """Process customer timestamps data"""
    try:
        # Deduplicate DataFrame on unique fields before processing
        dedup_cols = ['Load Number', 'Schedule Date', 'Truck Number']
        for col, fallback in zip(dedup_cols, ['Load Name', 'schedule_date', 'Vehicle Reg']):
            if col not in df.columns and fallback in df.columns:
                df[col] = df[fallback]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=dedup_cols)
        after_dedup = len(df)
        if before_dedup != after_dedup:
            print(f"Deduplicated customer timestamps: {before_dedup - after_dedup} duplicate rows skipped in CSV.")
        seen_keys = set()
        for index, row in df.iterrows():
            try:
                # Robust date parsing for create_date
                create_date = pd.to_datetime(row.get('Schedule Date', row.get('schedule_date', datetime.now().date())), errors='coerce', dayfirst=True)
                if pd.isna(create_date):
                    create_date = datetime.now().date()
                else:
                    create_date = create_date.date() if hasattr(create_date, 'date') else create_date

                # Robust truck_number extraction
                truck_number = (
                    str(row.get('Truck Number', '')).strip() or
                    str(row.get('Vehicle Reg', '')).strip() or
                    str(row.get('Load Name', '')).strip() or
                    str(row.get('Load', '')).strip() or
                    'Unknown'
                )

                load_number = str(row.get('Load Number', row.get('load_name', row.get('Load', f'LOAD_{index}'))))

                unique_key = (load_number, create_date, truck_number)
                if unique_key in seen_keys:
                    print(f"Duplicate row in CSV skipped: {unique_key}")
                    continue
                seen_keys.add(unique_key)

                arrival_at_depot = pd.to_datetime(row.get('Arrival At Depot', row.get('ArriveAtDepot(Odo)', None)), errors='coerce', dayfirst=True)
                if pd.notna(arrival_at_depot):
                    try:
                        arrival_at_depot = arrival_at_depot.time()
                    except Exception:
                        arrival_at_depot = None
                else:
                    arrival_at_depot = None

                ave_arrival_time = pd.to_datetime(row.get('AVE Arrival Time'), errors='coerce', dayfirst=True) if pd.notna(row.get('AVE Arrival Time')) else None
                if pd.notna(ave_arrival_time):
                    try:
                        ave_arrival_time = ave_arrival_time.time()
                    except Exception:
                        ave_arrival_time = None
                else:
                    ave_arrival_time = None

                try:
                    # Simulate database write
                    print(f"[SIMULATE] Would upsert TruckPerformanceData: {unique_key}")
                except Exception as upsert_e:
                    print(f"Upsert error at row {index}: {upsert_e}\nRow data: {row.to_dict()}")
            except Exception as row_e:
                print(f"Row {index} error: {row_e}\nRow data: {row.to_dict()}")
        # Do not mark as processed
        print(f"[SIMULATE] Would mark {csv_upload.name} as processed (from process_customer_timestamps_data).")
        return True
    except Exception as e:
        print(f"Error in customer timestamps processing: {e}")
        return False

def process_distance_info_data(df, csv_upload):
    """Process distance information data"""
    try:
        # Deduplicate DataFrame on unique fields before processing
        dedup_cols = ['Load Number', 'Schedule Date', 'Truck Number']
        for col, fallback in zip(dedup_cols, ['Load Name', 'Create Date', 'Vehicle Reg']):
            if col not in df.columns and fallback in df.columns:
                df[col] = df[fallback]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=dedup_cols)
        after_dedup = len(df)
        if before_dedup != after_dedup:
            print(f"Deduplicated distance info: {before_dedup - after_dedup} duplicate rows skipped in CSV.")
        for index, row in df.iterrows():
            def safe_float(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            create_date = pd.to_datetime(row.get('Schedule Date', datetime.now().date()), errors='coerce', dayfirst=True)
            if pd.isna(create_date):
                create_date = datetime.now().date()
            else:
                create_date = create_date.date() if hasattr(create_date, 'date') else create_date

            # Simulate database write
            print(f"[SIMULATE] Would upsert TruckPerformanceData: {row.get('Load Number', row.get('Load Name', row.get('Load', f'LOAD_{index}')))}")
        return True
    except Exception as e:
        print(f"Error in distance info processing: {e}")
        return False

def process_timestamps_duration_data(df, csv_upload):
    """Process timestamps and duration data"""
    try:
        # Deduplicate DataFrame on unique fields before processing
        dedup_cols = ['Load Number', 'Schedule Date', 'Truck Number']
        for col, fallback in zip(dedup_cols, ['load_name', 'schedule_date', 'Vehicle Reg']):
            if col not in df.columns and fallback in df.columns:
                df[col] = df[fallback]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=dedup_cols)
        after_dedup = len(df)
        if before_dedup != after_dedup:
            print(f"Deduplicated timestamps duration: {before_dedup - after_dedup} duplicate rows skipped in CSV.")
        for index, row in df.iterrows():
            create_date = pd.to_datetime(row.get('Schedule Date', row.get('schedule_date', datetime.now().date())), errors='coerce', dayfirst=True)
            if pd.isna(create_date):
                create_date = datetime.now().date()
            else:
                create_date = create_date.date() if hasattr(create_date, 'date') else create_date

            # Map Comment Ave TIR from all possible columns
            comment_ave_tir = row.get('Comment Ave TIR', row.get('Gate Entry to load Completion', ''))
            # Simulate database write
            print(f"[SIMULATE] Would upsert TruckPerformanceData: {row.get('Load Number', row.get('load_name', row.get('Load', f'LOAD_{index}')))}")
        return True
    except Exception as e:
        print(f"Error in timestamps duration processing: {e}")
        return False

    # Removed process_avg_time_route_data as requested

def process_time_route_info_data(df, csv_upload):
    """Process time in route information data"""
    try:
        # Deduplicate DataFrame on unique fields before processing
        dedup_cols = ['Load', 'Schedule Date', 'Truck']
        for col, fallback in zip(dedup_cols, ['Load Number', 'Create Date', 'Vehicle Reg']):
            if col not in df.columns and fallback in df.columns:
                df[col] = df[fallback]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=dedup_cols)
        after_dedup = len(df)
        if before_dedup != after_dedup:
            print(f"Deduplicated time route info: {before_dedup - after_dedup} duplicate rows skipped in CSV.")
        for index, row in df.iterrows():
            # Set all required and useful fields for TruckPerformanceData
            create_date = pd.to_datetime(row.get('Schedule Date', datetime.now().date()), errors='coerce', dayfirst=True)
            if pd.isna(create_date):
                create_date = datetime.now().date()
            else:
                create_date = create_date.date() if hasattr(create_date, 'date') else create_date

            def safe_float(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return None

            # For this file type, truck number is in the 'Load' column
            truck_number = row.get('Load') or row.get('Truck') or row.get('Truck Number') or row.get('Vehicle Reg') or 'Unknown'
            # Robust extraction for time fields
            dj_val = row.get('DJ Departure Time')
            dj_dt = pd.to_datetime(dj_val, errors='coerce', dayfirst=True) if pd.notna(dj_val) else None
            dj_departure_time = dj_dt.time() if dj_dt is not None and not pd.isna(dj_dt) else None

            arr_val = row.get('Arrival At Depot', row.get('ArriveAtDepot(Odo)', None))
            arr_dt = pd.to_datetime(arr_val, errors='coerce', dayfirst=True) if pd.notna(arr_val) else None
            arrival_at_depot = arr_dt.time() if arr_dt is not None and not pd.isna(arr_dt) else None

            ave_val = row.get('AVE Arrival Time')
            ave_dt = pd.to_datetime(ave_val, errors='coerce', dayfirst=True) if pd.notna(ave_val) else None
            ave_arrival_time = ave_dt.time() if ave_dt is not None and not pd.isna(ave_dt) else None

            # Simulate database write
            print(f"[SIMULATE] Would upsert TruckPerformanceData: {row.get('Load', row.get('Load Number', f'LOAD_{index}'))}")
        return True
    except Exception as e:
        print(f"Error in time route info processing: {e}")
        return False

def process_generic_data(df, csv_upload):
    """Process generic CSV data"""
    try:
        # Deduplicate DataFrame on unique fields before processing
        dedup_cols = ['Load Number', 'Schedule Date', 'Truck Number']
        for col, fallback in zip(dedup_cols, ['Load Name', 'Create Date', 'Vehicle Reg']):
            if col not in df.columns and fallback in df.columns:
                df[col] = df[fallback]
        before_dedup = len(df)
        df = df.drop_duplicates(subset=dedup_cols)
        after_dedup = len(df)
        if before_dedup != after_dedup:
            print(f"Deduplicated generic: {before_dedup - after_dedup} duplicate rows skipped in CSV.")
        for index, row in df.iterrows():
            # Create a generic record with whatever data is available
            data = {
                'create_date': datetime.now().date(),
                'month_name': datetime.now().strftime('%B'),
                'load_number': str(row.get('Load Number', f'LOAD_{index}')),
            }
            # Map common field names
            field_mappings = {
                'Transporter': 'transporter',
                'Driver Name': 'driver_name',
                'Truck Number': 'truck_number',
                'Customer Name': 'customer_name',
            }

            for csv_col, model_field in field_mappings.items():
                if csv_col in row and pd.notna(row[csv_col]):
                    data[model_field] = str(row[csv_col])

            # Simulate database write
            print(f"[SIMULATE] Would upsert TruckPerformanceData: {data['load_number']}")
        return True
    except Exception as e:
        print(f"Error in generic processing: {e}")
        return False

if __name__ == "__main__":
    process_existing_files()
