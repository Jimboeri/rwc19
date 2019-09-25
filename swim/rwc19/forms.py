from django import forms
from .models import Prediction, Game

#class ContactForm(forms.Form):
#    descr = forms.CharField(widget=forms.Textarea)

class PickDetailForm(forms.ModelForm):
    class Meta:
        model = Prediction
        fields = ['score1', 'score2']
        #widgets = {
        #    'descr': forms.Textarea(attrs={'rows': 3}),
        #}

class gameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['gamedate', 'score1', 'score2', 'started', 'finished']
        #widgets = {
        #    'descr': forms.Textarea(attrs={'rows': 3}),
        #}

