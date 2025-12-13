<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Truck Productivity Dashboard - Copilot Instructions

This is a Django web application for analyzing truck productivity data by combining multiple CSV files.

## Project Context

- **Framework**: Django 5.2.4
- **Purpose**: Analyze truck performance data from multiple CSV sources
- **Key Features**: CSV upload, data processing, dashboard visualization, reporting

## Code Style Guidelines

- Follow Django best practices and conventions
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Follow PEP 8 style guidelines
- Use type hints where appropriate

## Key Components

### Models (`dashboard/models.py`)
- `CSVUpload`: Tracks uploaded CSV files
- `TruckPerformanceData`: Main data model for truck performance metrics
- `ProductivitySummary`: Aggregated performance data

### Views (`dashboard/views.py`)
- Uses pandas for CSV processing
- Plotly for data visualization
- Excel export functionality

### Templates
- Bootstrap 5 for responsive design
- Plotly.js for interactive charts
- Font Awesome for icons

## Data Processing

- Support for multiple CSV formats (distance info, time routes, timestamps)
- Automatic data validation and error handling
- Efficiency score calculation based on time and distance performance

## Database Schema

- Uses Django ORM with SQLite (default)
- Foreign key relationships between uploads and performance data
- Proper indexing for performance queries

## When making changes:

1. Always run migrations after model changes
2. Test CSV upload functionality with sample data
3. Ensure charts render properly in templates
4. Validate Excel export functionality
5. Check responsive design on mobile devices

## Common Tasks

- Adding new CSV file types: Update `CSVUpload.UPLOAD_TYPES` and add processing function
- New chart types: Add to `create_performance_charts()` function
- Performance optimizations: Consider database indexing and query optimization
- UI improvements: Update Bootstrap classes and CSS in templates
