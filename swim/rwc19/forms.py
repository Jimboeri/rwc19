from django import forms
from .models import Prediction

#class ContactForm(forms.Form):
#    descr = forms.CharField(widget=forms.Textarea)

class PickDetailForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = ['score1', 'score1']
        #widgets = {
        #    'descr': forms.Textarea(attrs={'rows': 3}),
        #}

