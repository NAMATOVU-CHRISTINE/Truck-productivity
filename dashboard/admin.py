from django.contrib import admin
from .models import CSVUpload, TruckPerformanceData, ProductivitySummary


@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    list_display = ['name', 'upload_type', 'uploaded_at', 'processed']
    list_filter = ['upload_type', 'processed', 'uploaded_at']
    search_fields = ['name']
    readonly_fields = ['uploaded_at']


@admin.register(TruckPerformanceData)
class TruckPerformanceDataAdmin(admin.ModelAdmin):
    list_display = ['load_number', 'employee_id', 'create_date', 'transporter', 'customer_name', 'driver_name', 'truck_number', 'efficiency_score']
    list_filter = ['transporter', 'create_date', 'mode_of_capture', 'customer_name']
    search_fields = ['load_number', 'employee_id', 'driver_name', 'customer_name', 'truck_number', 'transporter']
    date_hierarchy = 'create_date'
    ordering = ['-create_date']
    readonly_fields = ['created_at', 'updated_at', 'total_distance', 'total_time', 'efficiency_score']


@admin.register(ProductivitySummary)
class ProductivitySummaryAdmin(admin.ModelAdmin):
    list_display = ['date_range_start', 'date_range_end', 'transporter', 'total_loads', 'avg_efficiency_score']
    list_filter = ['transporter', 'date_range_start']
    readonly_fields = ['created_at']
