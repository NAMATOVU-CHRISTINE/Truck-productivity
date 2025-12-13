# Truck Productivity Dashboard

A powerful Django-based analytics platform for tracking and visualizing truck fleet performance. This application processes various operational CSV logs to generate comprehensive insights on delivery times, route efficiency, and driver performance.

## Features

- **Multi-Source Data Integration**: Seamlessly combines data from 6 distinct CSV sources.
- **Real-time Progress Tracking**: visual tracking of truck journeys from Depot to Customer and back.
- **Performance Analytics**:
  - Efficiency Scores (Distance/Time)
  - On-time vs Delayed Deliveries
  - Budgeted vs Actual Metrics (Days, Kilometers)
- **Interactive Dashboard**: Modern, responsive UI with charts and key metrics.
- **Excel Reporting**: Generate detailed consolidated reports for offline analysis.

## Supported CSV Files

The system is designed to process the following 6 specific CSV file types:

1. **Depot Departures Information**: Core trip data including Driver, Vehicle, and planned departure times.
2. **Customer Timestamps**: Arrival and service times at customer locations (calculates D1, D2 distances).
3. **Distance Information**: Planned vs Actual distance data for route optimization.
4. **Timestamps and Duration**: detailed gate and load completion timestamps.
5. **Average Time in Route**: Historical average performance data.
6. **Time in Route Information**: Specific trip duration and deviation analysis.

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd truck-productivity
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a superuser (for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
   Access the dashboard at `http://127.0.0.1:8000/`.

## Usage

1. **Upload Data**: Navigate to the "Bulk Upload" page. You can upload any combination of the 6 supported file types.
2. **Auto-Processing**: The system automatically links records based on Load Number, Truck Number, and Date.
3. **Dashboard**: View high-level metrics on the main dashboard.
4. **Track Trucks**: Use the "Track Trucks" page to see the real-time status of active shipments.
5. **Export**: Go to "Export Excel" to download a full productivity report.

## Tech Stack

- **Backend**: Django (Python)
- **Database**: SQLite (default) / PostgreSQL (production ready)
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap 5)
- **Data Processing**: Pandas
- **Visualization**: Plotly.js, Chart.js

## License

This project is proprietary software for internal use.
