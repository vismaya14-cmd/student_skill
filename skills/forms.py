from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ServicePost, ServiceRequest, Message, Review

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'email', 'phone', 'skills_offered', 'location', 'bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell others about yourself...'}),
            'skills_offered': forms.TextInput(attrs={'placeholder': 'e.g. Python, Math Tutoring'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['email'].initial = self.instance.user.email
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile

class ServicePostForm(forms.ModelForm):
    custom_category = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter your category'}))

    class Meta:
        model = ServicePost
        fields = ['title', 'description', 'category', 'custom_category', 'price_type', 'price', 'location']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['category'].widget.attrs.update({'id': 'id_category'})
        self.fields['custom_category'].widget.attrs.update({'id': 'id_custom_category'})

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        custom = cleaned_data.get('custom_category')
        if category == 'other' and not custom:
            self.add_error('custom_category', 'Please specify your custom category.')
        if category == 'other' and custom:
            cleaned_data['category'] = custom
        return cleaned_data

class ServiceRequestForm(forms.ModelForm):
    custom_category = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter your category'}))

    class Meta:
        model = ServiceRequest
        fields = ['title', 'description', 'category', 'custom_category', 'budget']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['category'].widget.attrs.update({'id': 'id_category_req'})
        self.fields['custom_category'].widget.attrs.update({'id': 'id_custom_category_req'})

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        custom = cleaned_data.get('custom_category')
        if category == 'other' and not custom:
            self.add_error('custom_category', 'Please specify your custom category.')
        if category == 'other' and custom:
            cleaned_data['category'] = custom
        return cleaned_data

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message here...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({'class': 'form-control'})
        self.fields['content'].label = ""

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Stars") for i in range(5, 0, -1)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Share your experience...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
