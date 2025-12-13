"""
Merge all 5 truck productivity files into a final productivity table.
- Joins on Load/Truck Number and Date where possible
- Outputs a single CSV with all key columns
"""
import pandas as pd
from datetime import datetime

# File paths (update if needed)
files = {
    'depot': r'C:\Users\CHRISTINE\OneDrive\Desktop\Fix\media\uploads\1.Depot_Departures_Inf_1752480585396.csv',
    'customer': r'C:\Users\CHRISTINE\OneDrive\Desktop\Fix\media\uploads\2.Customer_Timestamps__1752480054194.csv',
    'distance': r'C:\Users\CHRISTINE\OneDrive\Desktop\Fix\media\uploads\3.Distance_Information_1752480636033.csv',
    'duration': r'C:\Users\CHRISTINE\OneDrive\Desktop\Fix\media\uploads\4.Timestamps_and_Durat_1752480667772.csv',
    'route': r'C:\Users\CHRISTINE\OneDrive\Desktop\Fix\media\uploads\5.Time_in_Route_Inform_1752490636583.csv',
}

# Read all files
f_depot = pd.read_csv(files['depot'])
f_customer = pd.read_csv(files['customer'])
f_distance = pd.read_csv(files['distance'])
f_duration = pd.read_csv(files['duration'])
f_route = pd.read_csv(files['route'])

# Standardize keys for merging
f_depot['key'] = f_depot['Load Name'].fillna(f_depot.get('Load Number', '')) + '_' + pd.to_datetime(f_depot['Schedule Date'], errors='coerce').astype(str)
f_customer['key'] = f_customer['load_name'].fillna(f_customer.get('Load Number', '')) + '_' + pd.to_datetime(f_customer['schedule_date'], errors='coerce').astype(str)
f_distance['key'] = f_distance['Load Name'].fillna(f_distance.get('Load Number', '')) + '_' + pd.to_datetime(f_distance['Schedule Date'], errors='coerce').astype(str)
f_duration['key'] = f_duration['load_name'].fillna(f_duration.get('Load Number', '')) + '_' + pd.to_datetime(f_duration['schedule_date'], errors='coerce').astype(str)
f_route['key'] = f_route['Load'].fillna(f_route.get('Load Number', '')) + '_' + pd.to_datetime(f_route['Schedule Date'], errors='coerce').astype(str)

# Merge all files on the key
final = f_depot.merge(f_customer, on='key', how='outer', suffixes=('', '_cust'))
final = final.merge(f_distance, on='key', how='outer', suffixes=('', '_dist'))
final = final.merge(f_duration, on='key', how='outer', suffixes=('', '_dur'))
final = final.merge(f_route, on='key', how='outer', suffixes=('', '_route'))

# Select and rename columns for final output
final_out = pd.DataFrame({
    'Date': final['Schedule Date'],
    'Month': pd.to_datetime(final['Schedule Date'], errors='coerce').dt.strftime('%B'),
    'Depot': final['Depot'],
    'Truck Number': final['Load Name'],
    'Driver': final['Driver Name'],
    'Customer': final['Customer'],
    'DJ Departure Time': final.get('DJ Departure Time', None),
    'Arrival At Depot': final.get('Arrival At Depot', final.get('ArriveAtDepot(Odo)', None)),
    'AVE Arrival Time': final.get('AVE Arrival Time', None),
    'D1': final.get('Depot Departure Odometer', final.get('D1', None)),
    'D2': final.get('Navigate To Customer Odometer', final.get('D2', None)),
    'D3': final.get('Arrived at Customer Odometer', final.get('D3', None)),
    'D4': final.get('Arrived At Depot Odometer', final.get('D4', None)),
    'Comment Ave TIR': final.get('Comment Ave TIR', final.get('Gate Entry to load Completion', None)),
    # Add more fields/calculations as needed
})

# Save to Excel and CSV
final_out.to_excel('Final_Productivity_Merged.xlsx', index=False)
final_out.to_csv('Final_Productivity_Merged.csv', index=False)

print('Final productivity table saved as Final_Productivity_Merged.xlsx and .csv')
