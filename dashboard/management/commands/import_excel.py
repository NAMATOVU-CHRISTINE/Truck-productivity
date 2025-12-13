from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime, parse_date
import pandas as pd
import os
from datetime import datetime
from dashboard.models import TruckPerformanceData, CSVUpload


class Command(BaseCommand):
    help = 'Import truck productivity data from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')
        parser.add_argument(
            '--sheet',
            type=str,
            default=0,
            help='Sheet name or index (default: 0 for first sheet)'
        )

    def clean_datetime_string(self, dt_str):
        """Clean and parse datetime strings from Excel"""
        if pd.isna(dt_str) or dt_str == '' or dt_str is None:
            return None
        
        dt_str = str(dt_str).strip()
        
        try:
            if isinstance(dt_str, str) and '/' in dt_str:
                if len(dt_str.split('/')[2].split()[0]) == 2:  # 2-digit year
                    dt_obj = datetime.strptime(dt_str, '%m/%d/%y %H:%M')
                else:  # 4-digit year
                    dt_obj = datetime.strptime(dt_str, '%m/%d/%Y %H:%M')
                return dt_obj
            else:
                return parse_datetime(dt_str)
        except (ValueError, AttributeError):
            return None

    def clean_date_string(self, date_str):
        """Clean and parse date strings from Excel"""
        if pd.isna(date_str) or date_str == '' or date_str is None:
            return None
        
        date_str = str(date_str).strip()
        
        try:
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

    def clean_numeric_value(self, value):
        """Clean and convert numeric values"""
        if pd.isna(value) or value == '' or value is None:
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def clean_integer_value(self, value):
        """Clean and convert integer values"""
        if pd.isna(value) or value == '' or value is None:
            return None
        
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        sheet = options['sheet']
        
        if not os.path.exists(excel_file):
            raise CommandError(f'File "{excel_file}" does not exist.')

        self.stdout.write(f'Reading Excel file: {excel_file}')
        
        try:
            # Read the file - handle both Excel and CSV
            if excel_file.lower().endswith('.csv'):
                df = pd.read_csv(excel_file)
            else:
                df = pd.read_excel(excel_file, sheet_name=sheet)
            self.stdout.write(f'Found {len(df)} rows in file')
            
            # Display column names
            self.stdout.write('Columns in file:')
            for i, col in enumerate(df.columns):
                self.stdout.write(f'{i+1}. {col}')

            # Create a CSV upload record to track this import
            csv_upload = CSVUpload.objects.create(
                name=f'Data Import - {os.path.basename(excel_file)}',
                upload_type='other',
                processed=True
            )

            successful_imports = 0
            errors = []
    
            for index, row in df.iterrows():
                try:
                    # Check if record already exists (avoid duplicates)
                    existing = TruckPerformanceData.objects.filter(
                        load_number=str(row.get('Load Number', '')).strip(),
                        create_date=self.clean_date_string(row.get('Create Date')),
                        truck_number=str(row.get('Truck Number', '')).strip()
                    ).first()
                    
                    if existing:
                        self.stdout.write(f'Skipping duplicate record: {existing.load_number} - {existing.truck_number}')
                        continue
                    
                    # Create TruckPerformanceData object
                    truck_data = TruckPerformanceData(
                        csv_upload=csv_upload,
                        
                        # Core fields
                        create_date=self.clean_date_string(row.get('Create Date')),
                        month_name=str(row.get('Month Name', '')).strip() if not pd.isna(row.get('Month Name')) else '',
                        transporter=str(row.get('Transporter', '')).strip() if not pd.isna(row.get('Transporter')) else '',
                        load_number=str(row.get('Load Number', '')).strip() if not pd.isna(row.get('Load Number')) else '',
                        mode_of_capture=str(row.get('Mode Of Capture', '')).strip() if not pd.isna(row.get('Mode Of Capture')) else '',
                        driver_name=str(row.get('Driver Name', '')).strip() if not pd.isna(row.get('Driver Name')) else '',
                        truck_number=str(row.get('Truck Number', '')).strip() if not pd.isna(row.get('Truck Number')) else '',
                        customer_name=str(row.get('Customer Name', '')).strip() if not pd.isna(row.get('Customer Name')) else '',
                        
                        # Timing fields
                        dj_departure_time=self.clean_datetime_string(row.get('DJ Departure Time')),
                        departure_deviation_min=self.clean_integer_value(row.get('Depature Deviation (min)')),
                        ave_departure=self.clean_integer_value(row.get('AVE Departure')),
                        comment_ave_departure=str(row.get('Comment  AVE Departure', '')).strip() if not pd.isna(row.get('Comment  AVE Departure')) else '',
                        
                        # Customer service fields
                        arrival_at_customer=self.clean_datetime_string(row.get('Arrival At Customer')),
                        departure_time_from_customer=self.clean_datetime_string(row.get('Departure Time from Customer')),
                        service_time_at_customer=self.clean_integer_value(row.get('Service Time At Customer')),
                        comment_tat=str(row.get('Comment  TAT', '')).strip() if not pd.isna(row.get('Comment  TAT')) else '',
                        
                        # Depot return fields
                        arrival_at_depot=self.clean_datetime_string(row.get('Arrival At Depot')),
                        ave_arrival_time=self.clean_integer_value(row.get('AVE Arrival Time')),
                        
                        # Distance fields
                        d1=self.clean_numeric_value(row.get('D1')),
                        d2=self.clean_numeric_value(row.get('D2')),
                        d3=self.clean_numeric_value(row.get('D3')),
                        d4=self.clean_numeric_value(row.get('D4')),
                        
                        # Comments
                        comment_ave_tir=str(row.get('Comment Ave TIR', '')).strip() if not pd.isna(row.get('Comment Ave TIR')) else '',
                    )
                    
                    # Validate required fields
                    if not truck_data.create_date:
                        errors.append(f'Row {index + 2}: Missing create_date')
                        continue
                        
                    if not truck_data.load_number:
                        errors.append(f'Row {index + 2}: Missing load_number')
                        continue
                    
                    # Save the object
                    truck_data.save()
                    successful_imports += 1
                    
                    if successful_imports % 50 == 0:
                        self.stdout.write(f'Imported {successful_imports} records...')
                        
                except Exception as e:
                    errors.append(f'Row {index + 2}: {str(e)}')
                    continue
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(f'Import completed! Successfully imported: {successful_imports} records')
            )
            
            if errors:
                self.stdout.write(
                    self.style.WARNING(f'Errors encountered: {len(errors)}')
                )
                self.stdout.write('First 10 errors:')
                for error in errors[:10]:
                    self.stdout.write(f'  - {error}')
            
        except Exception as e:
            raise CommandError(f'Error reading Excel file: {str(e)}')
        return successful_imports, errors
        except pd.errors.EmptyDataError:
            