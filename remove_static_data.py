#!/usr/bin/env python
"""
Remove All Static Data - Clean Database Script
This script safely removes all truck performance data while preserving the database structure
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'truck_productivity.settings')
django.setup()

from dashboard.models import TruckPerformanceData, CSVUpload

def remove_all_static_data():
    """Remove all static data from the database"""
    
    print("="*60)
    print("REMOVING ALL STATIC DATA FROM SYSTEM")
    print("="*60)
    
    # 1. CHECK CURRENT DATA
    print("\n1. CURRENT DATA STATUS")
    print("-" * 25)
    
    truck_records = TruckPerformanceData.objects.count()
    csv_uploads = CSVUpload.objects.count()
    
    print(f"Truck performance records: {truck_records:,}")
    print(f"CSV upload records: {csv_uploads:,}")
    
    if truck_records == 0 and csv_uploads == 0:
        print("✅ No static data found - database is already clean")
        return
    
    # 2. CONFIRM DELETION
    print(f"\n⚠️  WARNING: This will delete ALL {truck_records:,} truck records and {csv_uploads:,} CSV upload records")
    print("This action cannot be undone!")
    
    confirmation = input("\nType 'DELETE ALL DATA' to confirm: ")
    
    if confirmation != 'DELETE ALL DATA':
        print("❌ Operation cancelled - no data was deleted")
        return
    
    # 3. DELETE ALL DATA
    print("\n2. DELETING ALL STATIC DATA")
    print("-" * 30)
    
    try:
        # Delete all truck performance data
        print("Deleting truck performance records...")
        deleted_trucks = TruckPerformanceData.objects.all().delete()
        print(f"✅ Deleted {deleted_trucks[0]:,} truck performance records")
        
        # Delete all CSV upload records
        print("Deleting CSV upload records...")
        deleted_csvs = CSVUpload.objects.all().delete()
        print(f"✅ Deleted {deleted_csvs[0]:,} CSV upload records")
        
    except Exception as e:
        print(f"❌ Error during deletion: {e}")
        return
    
    # 4. VERIFY CLEAN DATABASE
    print("\n3. VERIFICATION")
    print("-" * 15)
    
    remaining_trucks = TruckPerformanceData.objects.count()
    remaining_csvs = CSVUpload.objects.count()
    
    print(f"Remaining truck records: {remaining_trucks}")
    print(f"Remaining CSV records: {remaining_csvs}")
    
    if remaining_trucks == 0 and remaining_csvs == 0:
        print("✅ SUCCESS: All static data has been removed")
    else:
        print("⚠️  WARNING: Some records may still remain")
    
    # 5. CLEAN UP MEDIA FILES (OPTIONAL)
    print("\n4. MEDIA FILES CLEANUP")
    print("-" * 25)
    
    import os
    import glob
    
    media_path = "media/uploads/"
    if os.path.exists(media_path):
        csv_files = glob.glob(os.path.join(media_path, "*.csv"))
        excel_files = glob.glob(os.path.join(media_path, "*.xlsx"))
        
        total_files = len(csv_files) + len(excel_files)
        
        if total_files > 0:
            print(f"Found {total_files} uploaded files in media/uploads/")
            clean_media = input("Delete uploaded files too? (y/n): ").lower()
            
            if clean_media == 'y':
                deleted_files = 0
                for file_path in csv_files + excel_files:
                    try:
                        os.remove(file_path)
                        deleted_files += 1
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
                
                print(f"✅ Deleted {deleted_files} media files")
            else:
                print("📁 Media files kept (uploaded CSV/Excel files remain)")
        else:
            print("📁 No media files found to clean")
    else:
        print("📁 Media uploads directory not found")
    
    # 6. RESET DATABASE SEQUENCES (if using PostgreSQL)
    print("\n5. DATABASE MAINTENANCE")
    print("-" * 25)
    
    try:
        from django.db import connection
        
        # Reset auto-increment counters
        with connection.cursor() as cursor:
            # For SQLite
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='dashboard_truckperformancedata';")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='dashboard_csvupload';")
        
        print("✅ Database sequences reset")
        
    except Exception as e:
        print(f"⚠️  Note: Could not reset sequences: {e}")
    
    # 7. FINAL STATUS
    print("\n" + "="*60)
    print("🎉 ALL STATIC DATA SUCCESSFULLY REMOVED")
    print("="*60)
    
    print("\n📋 WHAT'S BEEN CLEANED:")
    print("• All truck performance records deleted")
    print("• All CSV upload records deleted") 
    print("• Database sequences reset")
    if 'clean_media' in locals() and clean_media == 'y':
        print("• Uploaded files removed")
    
    print("\n📋 WHAT'S PRESERVED:")
    print("• Database structure and tables")
    print("• Django models and migrations")
    print("• Application code and settings")
    print("• Web interface functionality")
    
    print("\n🚀 SYSTEM IS NOW CLEAN AND READY FOR:")
    print("• Fresh CSV data uploads")
    print("• New truck performance data")
    print("• Clean dashboard display")
    print("• Production deployment")
    
    print("\n💡 NEXT STEPS:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Access dashboard: http://localhost:8000")
    print("3. Upload new CSV files through the web interface")
    print("4. Begin fresh data processing")

if __name__ == "__main__":
    remove_all_static_data()
