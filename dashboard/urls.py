
from django.urls import path
from . import views
from .export_utils import export_excel_report
from django.contrib.auth import views as auth_views

app_name = 'dashboard'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='dashboard/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='dashboard:login'), name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alias'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),

    path('reports/', views.reports_view, name='reports'),
    path('clear-data/', views.clear_all_data, name='clear_data'),
    path('tracking/', views.truck_tracking_view, name='truck_tracking'),
    path('tracking/<int:truck_id>/', views.truck_detail_tracking, name='truck_detail_tracking'),
    path('api/truck-status/', views.truck_status_api, name='truck_status_api'),
    path('export/', export_excel_report, name='export_excel'),
    path('download-report/<int:upload_id>/', views.download_report, name='download_report'),
]
