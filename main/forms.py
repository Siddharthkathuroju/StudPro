from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Group, LearningTrack, UploadedFile, GroupMessage, Connection, DirectMessage, VideoCallSession, Folder

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(user=user)
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'location', 'birth_date', 'avatar',
            'phone_number', 'website', 'linkedin', 'github',
            'education', 'institution', 'graduation_year', 'major',
            'skills', 'interests', 'hobbies',
            'current_position', 'company', 'experience_years',
            'twitter', 'instagram', 'facebook',
            'languages', 'certifications'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'graduation_year': forms.NumberInput(attrs={'min': 1900, 'max': 2030}),
            'experience_years': forms.NumberInput(attrs={'min': 0, 'max': 50}),
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'education': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your educational background...'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., Python, JavaScript, Machine Learning...'}),
            'interests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your areas of interest...'}),
            'hobbies': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your hobbies and activities...'}),
            'certifications': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your certifications and achievements...'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+1234567890'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com'}),
            'linkedin': forms.URLInput(attrs={'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'github': forms.URLInput(attrs={'placeholder': 'https://github.com/yourusername'}),
            'twitter': forms.URLInput(attrs={'placeholder': 'https://twitter.com/yourusername'}),
            'instagram': forms.URLInput(attrs={'placeholder': 'https://instagram.com/yourusername'}),
            'facebook': forms.URLInput(attrs={'placeholder': 'https://facebook.com/yourusername'}),
            'languages': forms.TextInput(attrs={'placeholder': 'English, Spanish, French...'}),
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class LearningTrackForm(forms.ModelForm):
    class Meta:
        model = LearningTrack
        fields = ['title', 'description', 'difficulty']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Add a description for this file...',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        current_folder = kwargs.pop('current_folder', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Add folder field with user's folders
            self.fields['folder'] = forms.ModelChoiceField(
                queryset=Folder.objects.filter(user=user),
                required=False,
                empty_label="Root Directory",
                widget=forms.Select(attrs={
                    'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })
            )
            
            # Set current folder as default if provided
            if current_folder:
                self.fields['folder'].initial = current_folder
    
    def clean(self):
        cleaned_data = super().clean()
        # Ensure folder is properly set from POST data if not in cleaned_data
        if not cleaned_data.get('folder') and self.data.get('folder'):
            try:
                folder_id = int(self.data.get('folder'))
                cleaned_data['folder'] = Folder.objects.get(id=folder_id)
            except (ValueError, Folder.DoesNotExist):
                pass
        return cleaned_data

class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Enter folder name...',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        parent_folder = kwargs.pop('parent_folder', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Add parent folder field
            self.fields['parent_folder'] = forms.ModelChoiceField(
                queryset=Folder.objects.filter(user=user),
                required=False,
                empty_label="Root Directory",
                widget=forms.Select(attrs={
                    'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                })
            )
            
            # Set parent folder as default if provided
            if parent_folder:
                self.fields['parent_folder'].initial = parent_folder

class GroupMessageForm(forms.ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['message', 'media_file']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Type your message...',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none'
            }),
            'media_file': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*,video/*,.pdf,.doc,.docx,.txt,.zip,.rar'
            }),
        }
    
    def clean_media_file(self):
        media_file = self.cleaned_data.get('media_file')
        if media_file:
            # Check file size (max 10MB)
            if media_file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('File size must be less than 10MB.')
            
            # Check file type
            allowed_types = [
                # Images
                'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
                # Videos
                'video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv', 'video/webm',
                # Documents
                'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain', 'application/zip', 'application/x-rar-compressed'
            ]
            
            if media_file.content_type not in allowed_types:
                raise forms.ValidationError('File type not supported. Please upload images, videos, or documents.')
        
        return media_file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set message type based on file
        if instance.media_file:
            content_type = instance.media_file.content_type
            if content_type.startswith('image/'):
                instance.message_type = 'image'
            elif content_type.startswith('video/'):
                instance.message_type = 'video'
            else:
                instance.message_type = 'file'
        
        if commit:
            instance.save()
        return instance

class GroupSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search groups...',
            'class': 'w-full p-2 border border-gray-300 rounded-lg'
        })
    )
    privacy = forms.ChoiceField(
        choices=[('', 'All'), ('public', 'Public'), ('private', 'Private')],
        required=False,
        widget=forms.Select(attrs={'class': 'p-2 border border-gray-300 rounded-lg'})
    )

class ConnectionRequestForm(forms.ModelForm):
    class Meta:
        model = Connection
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Write a personalized message to connect...',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }

class DirectMessageForm(forms.ModelForm):
    class Meta:
        model = DirectMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Type your message...',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }

class VideoCallForm(forms.ModelForm):
    class Meta:
        model = VideoCallSession
        fields = ['title', 'description', 'scheduled_time', 'duration']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Call title',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What will you discuss?',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'scheduled_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'duration': forms.NumberInput(attrs={
                'min': 15,
                'max': 120,
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
        }

class UserSearchForm(forms.Form):
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search users by name, skills, or interests...',
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    skills = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Filter by skills (e.g., Python, JavaScript)',
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
