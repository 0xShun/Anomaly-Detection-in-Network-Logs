from django import forms

class CalibrationForm(forms.Form):
    domain = forms.CharField(required=False, max_length=100)
    model_version = forms.CharField(required=False, max_length=100)
    objective = forms.ChoiceField(
        choices=[('f1', 'F1 Score (Balanced)'), ('target_fp', 'Target False Positive Rate')],
        required=False
    )
    target_fp = forms.FloatField(required=False)

# Minimal stub form to allow local setup and testing. Replace with full form logic as needed.
