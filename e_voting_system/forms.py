from django import forms


class LoginForm(forms.Form):
    PIN = forms.CharField(max_length=10, min_length=10, required=1,
                          widget=forms.TextInput(attrs={'id': 'pin', 'placeholder': '1240032119'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'password', 'placeholder': 'password'}))


DEGREES = (('BSC', 'لیسانس'), ('MSC', 'فوق لیسانس'), ('PHD', 'دکترا'))
