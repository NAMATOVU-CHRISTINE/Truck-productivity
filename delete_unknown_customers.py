from dashboard.models import TruckPerformanceData

# Delete all records with 'Unknown Customer' in the customer_name field
count, _ = TruckPerformanceData.objects.filter(customer_name__iexact='Unknown Customer').delete()
print(f"Deleted {count} records with 'Unknown Customer'.")
