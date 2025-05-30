from django import forms
from .models import PersonalAttendanceSetting

class PersonalAttendanceSettingForm(forms.ModelForm):
    class Meta:
        model = PersonalAttendanceSetting
        fields = ['user', 'date', 'checkin_time']