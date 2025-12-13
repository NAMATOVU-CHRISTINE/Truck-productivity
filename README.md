# Truck Productivity Dashboard

A Django web application for analyzing truck productivity data by combining multiple CSV files to generate comprehensive performance reports.

## Features

- **CSV File Upload**: Upload multiple types of CSV files (Distance Information, Time in Route, Timestamps, etc.)
- **Data Processing**: Automatically processes and combines data from different CSV sources
- **Interactive Dashboard**: Visual dashboard with key performance metrics
- **Performance Reports**: Detailed reports with filtering and export capabilities
- **Data Visualization**: Charts and graphs using Plotly for better insights
- **Excel Export**: Export processed data to Excel for further analysis

## Supported CSV File Types

1. **Distance Information**: Contains planned vs actual distance data
2. **Time in Route Information**: Contains time performance metrics
3. **Timestamps and Duration**: Contains timing data for various milestones
4. **Average Time in Route**: Contains customer-level performance summaries

## Installation

1. Install Python 3.8 or higher
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Load sample data (optional):
   ```bash
   python load_sample_data.py
   ```

5. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

Start the development server:
```bash
python manage.py runserver
```

Access the application at: http://127.0.0.1:8000/

## Usage

1. **Upload Data**: Go to the Upload page and select your CSV files
2. **View Dashboard**: The main dashboard shows key metrics and depot performance
3. **Generate Reports**: Use the Reports page to filter data and view detailed analytics
4. **Export Data**: Export processed data to Excel for external analysis

## CSV File Format Requirements

### Distance Information CSV
Required columns:
- Schedule Date
- Depot
- Load Name
- Driver Name
- Vehicle Reg
- Customer
- PlannedDistanceToCustomer
- Distance Difference (Planned vs DJ)

### Time in Route Information CSV
Required columns:
- Schedule Date
- Depot Code
- Load
- Driver
- Customer
- Time in Route (min)
- Planned Time in Route (min)
- Time In Route Difference ( DJ - Planned)

### Timestamps and Duration CSV
Required columns:
- schedule_date
- Depot
- load_name
- Load StartTime (Pre-Trip Start)
- GateManifestTime
- LoadCompleted

## Project Structure

```
truck_productivity/
├── dashboard/              # Main dashboard app
│   ├── models.py          # Database models
│   ├── views.py           # View logic
│   ├── forms.py           # Form definitions
│   ├── templates/         # HTML templates
│   └── admin.py           # Admin interface
├── truck_productivity/     # Project settings
├── static/                # Static files (CSS, JS)
├── media/                 # Uploaded files
├── manage.py              # Django management script
├── load_sample_data.py    # Sample data loader
└── requirements.txt       # Python dependencies
```

## Key Features

- **Efficiency Scoring**: Automatic calculation of efficiency scores based on time and distance performance
- **Performance Tracking**: Track on-time vs delayed deliveries
- **Depot Comparison**: Compare performance across different depots
- **Data Validation**: Automatic data validation and error handling during CSV processing
- **Responsive Design**: Mobile-friendly interface using Bootstrap

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is for internal use and data analysis purposes.
