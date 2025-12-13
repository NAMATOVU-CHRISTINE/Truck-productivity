from django.core.management.base import BaseCommand
from dashboard.models import TruckPerformanceData
import pandas as pd
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Merge all productivity CSVs and update TruckPerformanceData with merged results.'

    def handle(self, *args, **options):
        base_path = r'C:\Users\CHRISTINE\OneDrive\Desktop\Fix\media\uploads'
        files = {
            'depot': os.path.join(base_path, '1.Depot_Departures_Inf_1752480585396.csv'),
            'customer': os.path.join(base_path, '2.Customer_Timestamps__1752480054194.csv'),
            'distance': os.path.join(base_path, '3.Distance_Information_1752480636033.csv'),
            'duration': os.path.join(base_path, '4.Timestamps_and_Durat_1752480667772.csv'),
            'route': os.path.join(base_path, '5.Time_in_Route_Inform_1752490636583.csv'),
        }
        # Read all files
        f_depot = pd.read_csv(files['depot'])
        f_customer = pd.read_csv(files['customer'])
        f_distance = pd.read_csv(files['distance'])
        f_duration = pd.read_csv(files['duration'])
        f_route = pd.read_csv(files['route'])
        # Standardize keys for merging
        f_depot['key'] = f_depot['Load Name'].fillna(f_depot.get('Load Number', '')) + '_' + pd.to_datetime(f_depot['Schedule Date'], errors='coerce').astype(str)
        f_customer['key'] = f_customer['load_name'].fillna(f_customer.get('Load Number', '')) + '_' + pd.to_datetime(f_customer['schedule_date'], errors='coerce').astype(str)
        f_distance['key'] = f_distance['Load Name'].fillna(f_distance.get('Load Number', '')) + '_' + pd.to_datetime(f_distance['Schedule Date'], errors='coerce').astype(str)
        f_duration['key'] = f_duration['load_name'].fillna(f_duration.get('Load Number', '')) + '_' + pd.to_datetime(f_duration['schedule_date'], errors='coerce').astype(str)
        f_route['key'] = f_route['Load'].fillna(f_route.get('Load Number', '')) + '_' + pd.to_datetime(f_route['Schedule Date'], errors='coerce').astype(str)
        # Merge all files on the key
        final = f_depot.merge(f_customer, on='key', how='outer', suffixes=('', '_cust'))
        final = final.merge(f_distance, on='key', how='outer', suffixes=('', '_dist'))
        final = final.merge(f_duration, on='key', how='outer', suffixes=('', '_dur'))
        final = final.merge(f_route, on='key', how='outer', suffixes=('', '_route'))
        # For each row, update or create TruckPerformanceData
        for _, row in final.iterrows():
            load_number = row.get('Load Name') or row.get('load_name') or row.get('Load') or row.get('Load Number')
            if not load_number:
                continue
            create_date = pd.to_datetime(row.get('Schedule Date', row.get('schedule_date', None)), errors='coerce')
            if pd.isna(create_date):
                continue
            create_date = create_date.date() if hasattr(create_date, 'date') else create_date
            TruckPerformanceData.objects.update_or_create(
                load_number=str(load_number),
                create_date=create_date,
                defaults={
                    'month_name': create_date.strftime('%B'),
                    'transporter': row.get('Depot') or row.get('Depot Code') or row.get('Transporter', 'Unknown'),
                    'mode_of_capture': row.get('Mode Of Capture', 'Manual'),
                    'driver_name': row.get('Driver Name') or row.get('Driver'),
                    'truck_number': row.get('Load Name') or row.get('load_name') or row.get('Load'),
                    'customer_name': row.get('Customer'),
                    'dj_departure_time': row.get('DJ Departure Time'),
                    'arrival_at_depot': row.get('Arrival At Depot') or row.get('ArriveAtDepot(Odo)'),
                    'ave_arrival_time': row.get('AVE Arrival Time'),
                    'd1': row.get('Depot Departure Odometer') or row.get('D1'),
                    'd2': row.get('Navigate To Customer Odometer') or row.get('D2'),
                    'd3': row.get('Arrived at Customer Odometer') or row.get('D3'),
                    'd4': row.get('Arrived At Depot Odometer') or row.get('D4'),
                    'comment_ave_tir': row.get('Comment Ave TIR') or row.get('Gate Entry to load Completion'),
                    # Add more fields/calculations as needed
                }
            )
        self.stdout.write(self.style.SUCCESS('Merged and updated TruckPerformanceData from all 5 files.'))
