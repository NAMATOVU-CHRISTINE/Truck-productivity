
# Place DayDetail model after imports so 'models' is defined


from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone


class CSVUpload(models.Model):
    """Model to store uploaded CSV files"""
    UPLOAD_TYPES = [
        ('depot_departures', '1. Depot Departures Information'),
        ('customer_timestamps', '2. Customer Timestamps'),
        ('distance_info', '3. Distance Information'),
        ('timestamps_duration', '4. Timestamps and Duration'),
        ('time_route_info', '6. Time in Route Information'),
        ('other', 'Other CSV File')
    ]

    name = models.CharField(max_length=200)
    upload_type = models.CharField(max_length=50, choices=UPLOAD_TYPES)
    file = models.FileField(
        upload_to='uploads/', 
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.get_upload_type_display()}"


class TruckPerformanceData(models.Model):
    """Model to store truck performance data with specified attributes"""
    
    @property
    def total_wh(self) -> float:
        """Alias for total_working_hours for export compatibility."""
        return self.total_working_hours

    @property
    def tlp(self):
        """Placeholder for TLP field if not present in model."""
        return None
    
    total_working_hours = models.FloatField(null=True, blank=True, help_text="Total working hours in route (from data or calculated)")
    driver_rest_hours_in_route = models.FloatField(null=True, blank=True, help_text="Total driver rest hours in route (if available)")
    total_hour_route = models.FloatField(null=True, blank=True, help_text="Total hours in route (from departure to completion)")
    days_in_route_deviation = models.FloatField(null=True, blank=True, help_text="Deviation between actual and budgeted days in route")
    bud_days_in_route = models.FloatField(null=True, blank=True, help_text="Budgeted days in route (from planned DJ data)")
    actual_days_in_route = models.FloatField(null=True, blank=True, help_text="Actual days in route (from departure to completion)")
    clock_out = models.DateTimeField(null=True, blank=True, help_text="Time when load was completed (from LoadCompleted in timestamps file)")
    km_deviation = models.FloatField(null=True, blank=True, help_text="Difference between budgeted_kms and total_distance")
    planned_departure_time = models.DateTimeField(null=True, blank=True, help_text="Planned Departure Time")
    """Model to store truck performance data with specified attributes"""
    csv_upload = models.ForeignKey(CSVUpload, on_delete=models.CASCADE, related_name='performance_data', null=True, blank=True)
    
    # Core identification fields
    create_date = models.DateField()
    month_name = models.CharField(max_length=20)
    transporter = models.CharField(max_length=100)
    load_number = models.CharField(max_length=50)
    mode_of_capture = models.CharField(max_length=50, null=True, blank=True)
    driver_name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, null=True, blank=True, help_text="Employee/Driver ID")
    truck_number = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=200)
    
    # Departure and timing fields
    dj_departure_time = models.DateTimeField(null=True, blank=True, help_text="DJ Departure Time")
    clockin_time = models.DateTimeField(null=True, blank=True, help_text="Clock-In Time")
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
    # Remove fixed day fields; use DayDetail for flexible days

    # Distance fields (D1, D2, D3, D4)
    d1 = models.FloatField(null=True, blank=True, help_text="Distance 1")
    d2 = models.FloatField(null=True, blank=True, help_text="Distance 2")
    d3 = models.FloatField(null=True, blank=True, help_text="Distance 3")
    d4 = models.FloatField(null=True, blank=True, help_text="Distance 4")

    @property
    def D1(self):
        return self.d1
    @property
    def D2(self):
        return self.d2
    @property
    def D3(self):
        return self.d3
    @property
    def D4(self):
        return self.d4
    budgeted_kms = models.FloatField(null=True, blank=True, help_text="Planned distance to customer (from distance info)")
    
    # New fields for completeness
    planned_arrival_time = models.DateTimeField(null=True, blank=True, help_text="Planned Arrival Time at Depot")
    tlp_vol_hl = models.FloatField(null=True, blank=True, help_text="TLP Volume HL")

    # Comments and TIR
    comment_ave_tir = models.TextField(null=True, blank=True, help_text="Comment AVE TIR")
    
    # Status tracking for progress display
    STATUS_CHOICES = [
        ('pending', 'Pending Departure'),
        ('departed', 'Departed from Depot'),
        ('in_transit', 'In Transit to Customer'),
        ('at_customer', 'At Customer Location'),
        ('servicing', 'Servicing Customer'),
        ('returning', 'Returning to Depot'),
        ('completed', 'Journey Completed'),
        ('delayed', 'Delayed'),
    ]
    
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
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
        """Override save to calculate derived fields and set clock-in time as DJ Departure minus 30 minutes."""
        from datetime import timedelta
        from django.utils import timezone
        # Calculate total distance from D1, D2, D3, D4 properties
        # Calculate total distance from d1, d2, d3, d4
        distances = [self.d1, self.d2, self.d3, self.d4]
        valid_distances = [d for d in distances if d is not None]
        if valid_distances:
            self.total_distance = sum(valid_distances)
        # Calculate km_deviation as budgeted_kms - total_distance
        if self.budgeted_kms is not None and self.total_distance is not None:
            self.km_deviation = self.budgeted_kms - self.total_distance
        else:
            self.km_deviation = None
        # Make all datetime fields timezone-aware (UTC)
        def make_aware_if_needed(dt):
            if dt is None:
                return None
            if timezone.is_naive(dt):
                import datetime
                return timezone.make_aware(dt, timezone=datetime.timezone.utc)
            return dt
        if hasattr(self, 'dj_departure_time') and self.dj_departure_time:
            self.dj_departure_time = make_aware_if_needed(self.dj_departure_time)
        if hasattr(self, 'arrival_at_depot') and self.arrival_at_depot:
            self.arrival_at_depot = make_aware_if_needed(self.arrival_at_depot)
        if hasattr(self, 'arrival_at_customer') and self.arrival_at_customer:
            self.arrival_at_customer = make_aware_if_needed(self.arrival_at_customer)
        if hasattr(self, 'planned_departure_time') and self.planned_departure_time:
            self.planned_departure_time = make_aware_if_needed(self.planned_departure_time)
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
        # Always set clockin_time to DJ Departure minus 30 minutes if DJ Departure is present
        if self.dj_departure_time:
            try:
                self.clockin_time = make_aware_if_needed(self.dj_departure_time - timedelta(minutes=30))
            except Exception:
                self.clockin_time = None
        else:
            self.clockin_time = None
        # Calculate actual_days_in_route
        if self.dj_departure_time:
            end_time = self.clock_out or self.arrival_at_depot
            if end_time:
                delta = end_time - self.dj_departure_time
                self.actual_days_in_route = round(delta.total_seconds() / 86400, 2)
            else:
                self.actual_days_in_route = None
        else:
            self.actual_days_in_route = None

        # Calculate bud_days_in_route
        if hasattr(self, 'planned_departure_time') and hasattr(self, 'planned_arrival_time'):
            if self.planned_departure_time and self.planned_arrival_time:
                delta = self.planned_arrival_time - self.planned_departure_time
                self.bud_days_in_route = round(delta.total_seconds() / 86400, 2)
            else:
                self.bud_days_in_route = None
        else:
            self.bud_days_in_route = None
        # Calculate days_in_route_deviation
        if self.actual_days_in_route is not None and self.bud_days_in_route is not None:
            self.days_in_route_deviation = round(self.actual_days_in_route - self.bud_days_in_route, 2)
        else:
            self.days_in_route_deviation = None

        # Calculate total_hour_route
        if self.dj_departure_time:
            end_time = self.clock_out or self.arrival_at_depot
            if end_time:
                delta = end_time - self.dj_departure_time
                self.total_hour_route = round(delta.total_seconds() / 3600, 2)
            else:
                self.total_hour_route = None
        else:
            self.total_hour_route = None

        # Calculate total_working_hours as actual_days_in_route * 11
        if self.actual_days_in_route is not None:
            self.total_working_hours = round(self.actual_days_in_route * 11, 2)
        else:
            self.total_working_hours = None

        # Calculate driver_rest_hours_in_route
        if self.total_hour_route is not None and self.total_working_hours is not None:
            self.driver_rest_hours_in_route = round(self.total_hour_route - self.total_working_hours, 2)
        else:
            self.driver_rest_hours_in_route = None
        # Auto-determine status based on timestamps
        self.current_status = self.determine_current_status()
        super().save(*args, **kwargs)
    
    def determine_current_status(self):
        """Determine current status based on available timestamps"""
        from dashboard.views import make_naive
        now = timezone.now()
        now_naive = make_naive(now)
        dj_departure_time_naive = make_naive(self.dj_departure_time) if self.dj_departure_time else None
        arrival_at_depot_naive = make_naive(self.arrival_at_depot) if self.arrival_at_depot else None
        arrival_at_customer_naive = make_naive(self.arrival_at_customer) if self.arrival_at_customer else None
        departure_time_from_customer_naive = make_naive(self.departure_time_from_customer) if self.departure_time_from_customer else None
        # If no departure time is set, status is pending
        if not dj_departure_time_naive:
            return 'pending'
        # If journey is complete (returned to depot)
        if arrival_at_depot_naive:
            return 'completed'
        # If delayed (departure time is set but in the future or very recent)
        if dj_departure_time_naive and dj_departure_time_naive > now_naive:
            return 'delayed'

        # If departed from customer but not yet at depot
        if departure_time_from_customer_naive:
            return 'returning'

        # If at customer location
        if arrival_at_customer_naive and not departure_time_from_customer_naive:
            if self.service_time_at_customer and self.service_time_at_customer > 0:
                return 'servicing'
            else:
                return 'at_customer'
        
        # If departed from depot but not yet at customer
        if dj_departure_time_naive and not arrival_at_customer_naive:
            return 'in_transit'
        
        # If departure time is set but in the future or very recent
        if dj_departure_time_naive:
            return 'departed'
        
        # Default status
        return 'pending'
    
    def get_progress_percentage(self):
        """Calculate progress percentage based on status"""
        status_progress = {
            'pending': 0,
            'departed': 20,
            'in_transit': 40,
            'at_customer': 60,
            'servicing': 70,
            'returning': 85,
            'completed': 100,
            'delayed': 50,  # Arbitrary value for delayed
        }
        return status_progress.get(self.current_status, 0)
    
    def get_progress_steps(self):
        """Get progress steps for display"""
        steps = [
            {
                'name': 'Pending Departure',
                'icon': 'fas fa-clock',
                'status': 'pending',
                'completed': self.current_status != 'pending',
                'active': self.current_status == 'pending',
                'timestamp': None,
            },
            {
                'name': 'Departed from Depot',
                'icon': 'fas fa-truck',
                'status': 'departed',
                'completed': self.current_status not in ['pending'],
                'active': self.current_status == 'departed',
                'timestamp': self.dj_departure_time,
            },
            {
                'name': 'In Transit',
                'icon': 'fas fa-route',
                'status': 'in_transit',
                'completed': self.current_status not in ['pending', 'departed'],
                'active': self.current_status == 'in_transit',
                'timestamp': None,
            },
            {
                'name': 'At Customer',
                'icon': 'fas fa-map-marker-alt',
                'status': 'at_customer',
                'completed': self.current_status not in ['pending', 'departed', 'in_transit'],
                'active': self.current_status in ['at_customer', 'servicing'],
                'timestamp': self.arrival_at_customer,
            },
            {
                'name': 'Returning to Depot',
                'icon': 'fas fa-undo',
                'status': 'returning',
                'completed': self.current_status == 'completed',
                'active': self.current_status == 'returning',
                'timestamp': self.departure_time_from_customer,
            },
            {
                'name': 'Journey Completed',
                'icon': 'fas fa-check-circle',
                'status': 'completed',
                'completed': self.current_status == 'completed',
                'active': self.current_status == 'completed',
                'timestamp': self.arrival_at_depot,
            },
        ]
        return steps
    
    def calculate_progress_percentage(self):
        """Calculate progress percentage based on current status"""
        status_progress = {
            'pending': 0,
            'departed': 20,
            'in_transit': 40,
            'at_customer': 60,
            'servicing': 70,
            'returning': 85,
            'completed': 100,
            'delayed': 50,
        }
        return status_progress.get(self.current_status, 0)
    
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
    
    def __str__(self):
        return f"Summary {self.date_range_start} to {self.date_range_end}"
