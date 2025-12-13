from django.conf import settings
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import TruckPerformanceData, CSVUpload
from dashboard.views import process_csv_file
import pandas as pd

print("=== REPROCESSING ALL UPLOADED FILES ===")

# Clear all existing data
print("Clearing existing data...")
old_count = TruckPerformanceData.objects.count()
TruckPerformanceData.objects.all().delete()
print(f"Deleted {old_count} old records")

# Get all uploads
uploads = CSVUpload.objects.all()
print(f"Found {uploads.count()} uploads to process:")

for upload in uploads:
    print(f"\nProcessing: {upload.name} (Type: {upload.upload_type})")
    
    # Reset processed status
    upload.processed = False
    upload.save()
    
    # Process the file
    try:
        result = process_csv_file(upload)
        if result:
            new_count = TruckPerformanceData.objects.filter(csv_upload=upload).count()
            print(f"  ✓ Success: Created {new_count} records")
        else:
            print(f"  ✗ Failed to process")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Final summary
total_records = TruckPerformanceData.objects.count()
print(f"\n=== PROCESSING COMPLETE ===")
print(f"Total records created: {total_records}")

# Show sample of real data
print("\nSample of processed data:")
sample_records = TruckPerformanceData.objects.all()[:10]
for record in sample_records:
    print(f"  {record.load_number} | {record.driver_name} | {record.truck_number} | {record.transporter}")
