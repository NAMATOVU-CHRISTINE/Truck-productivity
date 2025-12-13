from django.db import models
from django.core.validators import FileExtensionValidator


class CSVUpload(models.Model):
    """Model to store uploaded CSV files"""
    UPLOAD_TYPES = [
        ('depot_departures', '1. Depot Departures Information'),
        ('customer_timestamps', '2. Customer Timestamps'),
        ('distance_info', '3. Distance Information'),
        ('timestamps_duration', '4. Timestamps and Duration'),
        ('time_route_info', '5. Time in Route Information'),
        ('other', 'Other CSV File'),
    ]

    name = models.CharField(max_length=200)
    upload_type = models.CharField(max_length=50, choices=UPLOAD_TYPES)
    file = models.FileField(
        upload_to='uploads/',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "CSV Upload"
        verbose_name_plural = "CSV Uploads"

    def __str__(self):
        return f"{self.name} - {self.get_upload_type_display()}"


class TruckPerformanceData(models.Model):
    """Model to store truck performance data with specified attributes"""
    csv_upload = models.ForeignKey(CSVUpload, on_delete=models.CASCADE, related_name='performance_data', null=True, blank=True)
    
    # Core identification fields
    create_date = models.DateField()
    month_name = models.CharField(max_length=20)
    transporter = models.CharField(max_length=100)
    load_number = models.CharField(max_length=50)
    mode_of_capture = models.CharField(max_length=50, null=True, blank=True)
    driver_name = models.CharField(max_length=100)
    truck_number = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=200)
    
    # Departure and timing fields
    dj_departure_time = models.DateTimeField(null=True, blank=True, help_text="DJ Departure Time")
    departure_deviation_min = models.IntegerField(null=True, blank=True, help_text="Departure Deviation (min)")
    ave_departure = models.IntegerField(null=True, blank=True, help_text="AVE Departure")
    comment_ave_departure = models.TextField(null=True, blank=True, help_text="Comment AVE Departure")
    
    # Customer arrival and service fields
    arrival_at_customer = models.DateTimeField(null=True, blank=True, help_text="Arrival At Customer")
    departure_time_from_customer = models.DateTimeField(null=True, blank=True, help_text="Departure Time from Customer")
    service_time_at_customer = models.IntegerField(null=True, blank=True, help_text="Service Time At Customer (minutes)")
    comment_tat = models.TextField(null=True, blank=True, help_text="Comment TAT (Turn Around Time)")
    
    # Depot return fields
    arrival_at_depot = models.DateTimeField(null=True, blank=True, help_text="Arrival At Depot")
    ave_arrival_time = models.IntegerField(null=True, blank=True, help_text="AVE Arrival Time")
    
    # Distance fields (D1, D2, D3, D4)
    d1 = models.FloatField(null=True, blank=True, help_text="Distance 1")
    d2 = models.FloatField(null=True, blank=True, help_text="Distance 2")
    d3 = models.FloatField(null=True, blank=True, help_text="Distance 3")
    d4 = models.FloatField(null=True, blank=True, help_text="Distance 4")
    
    # Comments and TIR
    comment_ave_tir = models.TextField(null=True, blank=True, help_text="Comment AVE TIR")
    
    # Calculated fields
    total_distance = models.FloatField(null=True, blank=True, help_text="Total Distance (D1+D2+D3+D4)")
    total_time = models.FloatField(null=True, blank=True, help_text="Total time from departure to depot arrival (hours)")
    delivery_time = models.FloatField(null=True, blank=True, help_text="Time from departure to customer arrival (hours)")
    efficiency_score = models.FloatField(null=True, blank=True, help_text="Distance per hour (km/h)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['load_number', 'create_date', 'truck_number']
        ordering = ['-create_date', 'transporter', 'load_number']
        verbose_name = "Truck Performance Data"
        verbose_name_plural = "Truck Performance Data"
    
    def save(self, *args, **kwargs):
        # Calculate total distance from D1, D2, D3, D4
        distances = [self.d1, self.d2, self.d3, self.d4]
        valid_distances = [d for d in distances if d is not None]
        if valid_distances:
            self.total_distance = sum(valid_distances)
        
        # Calculate total time using multiple time combinations
        if self.dj_departure_time and self.arrival_at_depot:
            time_diff = self.arrival_at_depot - self.dj_departure_time
            self.total_time = time_diff.total_seconds() / 3600  # Convert to hours
        elif self.dj_departure_time and self.arrival_at_customer:
            # Calculate delivery time if depot arrival not available
            time_diff = self.arrival_at_customer - self.dj_departure_time
            self.delivery_time = time_diff.total_seconds() / 3600
        
        # Calculate efficiency score (km per hour)
        if self.total_distance and self.total_time and self.total_time > 0:
            self.efficiency_score = self.total_distance / self.total_time
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.load_number} - {self.truck_number} - {self.driver_name}"
    
    @property
    def month_year(self):
        """Get formatted month and year"""
        return f"{self.month_name} {self.create_date.year}"


class ProductivitySummary(models.Model):
    """Model to store aggregated productivity metrics"""
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    transporter = models.CharField(max_length=100, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    
    total_loads = models.IntegerField(default=0)
    total_distance = models.FloatField(null=True, blank=True)
    total_time = models.FloatField(null=True, blank=True)
    avg_efficiency_score = models.FloatField(null=True, blank=True)
    
    # Performance metrics
    on_time_deliveries = models.IntegerField(default=0)
    delayed_deliveries = models.IntegerField(default=0)
    early_deliveries = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_range_end']
    
    Class Meta:
        verbose_name = "Productivity Summary"
        verbose_name_plural = "Productivity Summaries"
    def __str__(self):
        return f"Summary {self.date_range_start} to {self.date_range_end}"
