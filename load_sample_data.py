#!/usr/bin/env python
"""
Management command to load sample CSV data for testing the dashboard
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_path = Path(__file__).resolve().parent
sys.path.append(str(project_path))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import CSVUpload, TruckPerformanceData
import pandas as pd
from datetime import datetime


def load_sample_data():
    """Load sample data from the provided CSV attachments"""
    
    # Sample distance information data based on the attachment
    distance_data = [
        {
            'Schedule Date': '2025-07-10',
            'Depot': 'Jinja',
            'Load Name': 'BM113UORR',
            'Driver Name': 'Faluku Ssenjako',
            'Vehicle Reg': 'UBK 883R',
            'Sales Order': 'E19766',
            'Customer': 'TAN DISTRIBUTORS LTD-MBALE Tax No.: 1000926489',
            'PlannedDistanceToCustomer': 146.4,
            'Distance Difference (Planned vs DJ)': 266951.4,
            'Hired/Own': 'Own'
        },
        {
            'Schedule Date': '2025-07-10',
            'Depot': 'Jinja',
            'Load Name': 'BMF2EJARR',
            'Driver Name': 'KANYERRE SWAIBU',
            'Vehicle Reg': 'UBK 863R',
            'Sales Order': 'R16122',
            'Customer': 'Nakuya Enterprises Ltd Tax No.: 1000098344',
            'PlannedDistanceToCustomer': 79.9,
            'Distance Difference (Planned vs DJ)': 7.1,
            'Hired/Own': 'Hired'
        },
        {
            'Schedule Date': '2025-07-09',
            'Depot': 'Jinja',
            'Load Name': 'BM64LZ7RR',
            'Driver Name': 'Daniel Kiige',
            'Vehicle Reg': 'UBK 879R',
            'Sales Order': 'N05550',
            'Customer': 'Lira Resort Enterprises-Lira Tax No.: 1000378505',
            'PlannedDistanceToCustomer': 337.3,
            'Distance Difference (Planned vs DJ)': 61.7,
            'Hired/Own': 'Hired'
        },
        {
            'Schedule Date': '2025-07-08',
            'Depot': 'Jinja',
            'Load Name': 'BM6QGF6RR',
            'Driver Name': 'KABUYE MOSES',
            'Vehicle Reg': 'UBP 300H',
            'Sales Order': 'R16090',
            'Customer': 'Kato Investment Ltd -Mityana Tax No.: 1000098824',
            'PlannedDistanceToCustomer': 143.7,
            'Distance Difference (Planned vs DJ)': 8.3,
            'Hired/Own': 'Own'
        }
    ]
    
    # Sample time route data
    time_route_data = [
        {
            'Schedule Date': '2025-06-16',
            'Depot Code': 'O',
            'Load': 'OMGD02DRR',
            'Driver': 'KABANDA RONALD',
            'Customer': 'Sawan Distributors Ltd-Nabingo Tax No.: 1000186379',
            'Time in Route (min)': 25868,
            'Planned Time in Route (min)': 779,
            'Time In Route Difference ( DJ - Planned)': 25089
        },
        {
            'Schedule Date': '2025-06-19',
            'Depot Code': 'B',
            'Load': 'BMFRGE2RR',
            'Driver': 'WANDA BADIRU',
            'Customer': 'Blue Nile Distributors- Arua Tax No.: 1000202555',
            'Time in Route (min)': 26265,
            'Planned Time in Route (min)': 2606,
            'Time In Route Difference ( DJ - Planned)': 23659
        },
        {
            'Schedule Date': '2025-06-15',
            'Depot Code': 'O',
            'Load': 'OMRO0VHRR',
            'Driver': 'LURE FRED',
            'Customer': 'Sawan Distributors Ltd-Nabingo Tax No.: 1000186379',
            'Time in Route (min)': 19553,
            'Planned Time in Route (min)': 779,
            'Time In Route Difference ( DJ - Planned)': 18774
        }
    ]
    
    print("Loading sample distance information data...")
    
    # Create TruckPerformanceData from distance data
    for data in distance_data:
        try:
            schedule_date = datetime.strptime(data['Schedule Date'], '%Y-%m-%d').date()
            
            truck_data, created = TruckPerformanceData.objects.get_or_create(
                load_name=data['Load Name'],
                schedule_date=schedule_date,
                defaults={
                    'depot': data['Depot'],
                    'driver_name': data.get('Driver Name', ''),
                    'vehicle_reg': data.get('Vehicle Reg', ''),
                    'sales_order': data.get('Sales Order', ''),
                    'customer': data['Customer'],
                    'hired_or_own': data.get('Hired/Own', ''),
                    'planned_distance_to_customer': data.get('PlannedDistanceToCustomer'),
                    'distance_difference': data.get('Distance Difference (Planned vs DJ)'),
                }
            )
            
            if created:
                print(f"Created: {truck_data.load_name} - {truck_data.schedule_date}")
            else:
                print(f"Updated: {truck_data.load_name} - {truck_data.schedule_date}")
                
        except Exception as e:
            print(f"Error processing {data.get('Load Name', 'Unknown')}: {str(e)}")
    
    print("\nLoading sample time route data...")
    
    # Update with time route data
    for data in time_route_data:
        try:
            schedule_date = datetime.strptime(data['Schedule Date'], '%Y-%m-%d').date()
            
            truck_data, created = TruckPerformanceData.objects.get_or_create(
                load_name=data['Load'],
                schedule_date=schedule_date,
                defaults={
                    'depot': data['Depot Code'],
                    'driver_name': data.get('Driver', ''),
                    'customer': data['Customer'],
                }
            )
            
            # Update time metrics
            truck_data.actual_time_in_route = data.get('Time in Route (min)')
            truck_data.planned_time_in_route = data.get('Planned Time in Route (min)')
            truck_data.time_difference = data.get('Time In Route Difference ( DJ - Planned)')
            truck_data.save()
            
            print(f"Updated time data: {truck_data.load_name} - {truck_data.schedule_date}")
                
        except Exception as e:
            print(f"Error processing {data.get('Load', 'Unknown')}: {str(e)}")
    
    print(f"\nData loading complete! Total records: {TruckPerformanceData.objects.count()}")


if __name__ == '__main__':
    load_sample_data()
