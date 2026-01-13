from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Problem, Rating
import re


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('codeforces_handle', 'bio', 'profile_picture')


class AddProblemForm(forms.ModelForm):
    problem_id = forms.CharField(max_length=20, help_text='Format: <contestId><index>, e.g., 2184G')

    class Meta:
        model = Problem
        fields = ('problem_id',)

    def clean_problem_id(self):
        pid = self.cleaned_data['problem_id'].strip()
        # Validate pattern: digits then letters (e.g., 2184G or 1000A)
        if not re.match(r'^\d+[A-Za-z]+$', pid):
            raise forms.ValidationError('Invalid problem ID format. Example: 2184G')
        return pid


class RatingForm(forms.ModelForm):
    value = forms.IntegerField(min_value=0, max_value=10)

    class Meta:
        model = Rating
        fields = ('value',)
