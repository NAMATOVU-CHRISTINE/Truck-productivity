from django.conf import settings
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import TruckPerformanceData, CSVUpload
from dashboard.views import process_depot_departures
import pandas as pd

# Get the depot departures upload
depot_upload = CSVUpload.objects.filter(name__icontains='Depot').first()
print(f'Processing: {depot_upload.name}')

# Clear existing data from this upload to test fresh processing
old_records = TruckPerformanceData.objects.filter(csv_upload=depot_upload)
print(f'Deleting {old_records.count()} old records...')
old_records.delete()

# Read the file and process just first 3 rows for testing
df = pd.read_csv(depot_upload.file.path)
test_df = df.head(3)
print('Processing sample data:')
for _, row in test_df.iterrows():
    print(f'  Load: {row["Load Name"]}, Driver: {row["Driver Name"]}, Vehicle: {row["Vehicle Reg"]}')

# Reset upload status
depot_upload.processed = False
depot_upload.save()

# Process with our updated function
print('Processing with new function...')
result = process_depot_departures(test_df, depot_upload)
print(f'Processing result: {result}')

# Check what was created
new_records = TruckPerformanceData.objects.filter(csv_upload=depot_upload)
print(f'Created {new_records.count()} new records:')
for record in new_records:
    print(f'  Load: {record.load_number}, Driver: {record.driver_name}, Vehicle: {record.truck_number}, Depot: {record.transporter}')
