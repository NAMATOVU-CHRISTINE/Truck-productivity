from django import forms
from .models import CSVUpload


class CSVUploadForm(forms.ModelForm):
    class Meta:
        model = CSVUpload
        fields = ['name', 'upload_type', 'file']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a descriptive name for this upload'
            }),
            'upload_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.csv,.xlsx,.xls'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = 'Give this upload a meaningful name'
        self.fields['upload_type'].help_text = 'Select the type of data in your file'
        self.fields['file'].help_text = 'Upload CSV or Excel files only'


class BulkUploadForm(forms.Form):
    time_route_info_file = forms.FileField(
        label='5. Time in Route Information',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    """Form for uploading all 6 files at once"""

    depot_departures_file = forms.FileField(
        label='1. Depot Departures Information',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    customer_timestamps_file = forms.FileField(
        label='2. Customer Timestamps',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    distance_info_file = forms.FileField(
        label='3. Distance Information',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    timestamps_duration_file = forms.FileField(
        label='4. Timestamps and Duration',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )

    clockin_file = forms.FileField(
        label='6. Clock-In Information',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    
    def clean(self):
        cleaned_data = super().clean()
        files_uploaded = sum(1 for field_name, file_obj in cleaned_data.items() 
                           if field_name.endswith('_file') and file_obj)
        
        if files_uploaded == 0:
            raise forms.ValidationError("Please upload at least one file.")
        
        return cleaned_data


class DateRangeFilterForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        }),
        required=False
    )
    depot = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter depot name'
        }),
        required=False
    )
