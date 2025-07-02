from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Contact Information
    phone_number = models.CharField(max_length=15, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    
    # Education
    education = models.TextField(blank=True, help_text="Your educational background")
    institution = models.CharField(max_length=200, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    major = models.CharField(max_length=100, blank=True)
    
    # Skills and Interests
    skills = models.TextField(blank=True, help_text="Your technical skills and competencies")
    interests = models.TextField(blank=True, help_text="Your areas of interest")
    hobbies = models.TextField(blank=True, help_text="Your hobbies and activities")
    
    # Professional Information
    current_position = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    experience_years = models.IntegerField(null=True, blank=True)
    
    # Social Media
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    
    # Additional Information
    languages = models.CharField(max_length=200, blank=True, help_text="Languages you speak (comma-separated)")
    certifications = models.TextField(blank=True, help_text="Your certifications and achievements")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Group(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, related_name='study_groups')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(default=timezone.now)
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')
    max_members = models.IntegerField(default=50, help_text="Maximum number of members allowed")
    is_active = models.BooleanField(default=True)
    
    # Invite link functionality
    invite_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    invite_expires_at = models.DateTimeField(null=True, blank=True)
    invite_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Generate invite code if not exists
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)
    
    def generate_invite_code(self):
        """Generate a unique invite code"""
        while True:
            code = str(uuid.uuid4())[:8].upper()
            if not Group.objects.filter(invite_code=code).exists():
                return code
    
    def get_invite_link(self):
        """Get the full invite link"""
        if self.invite_code and self.invite_enabled:
            return f"/join-group-invite/{self.invite_code}/"
        return None
    
    def is_invite_valid(self):
        """Check if the invite link is still valid"""
        if not self.invite_enabled:
            return False
        if self.invite_expires_at and timezone.now() > self.invite_expires_at:
            return False
        return True
    
    def create_invite_link(self, expires_in_days=7):
        """Create a new invite link with expiration"""
        self.invite_code = self.generate_invite_code()
        self.invite_expires_at = timezone.now() + timedelta(days=expires_in_days)
        self.invite_enabled = True
        self.save()
        return self.get_invite_link()
    
    def disable_invite_link(self):
        """Disable the current invite link"""
        self.invite_enabled = False
        self.save()
    
    def member_count(self):
        return self.members.count()
    
    def is_full(self):
        return self.member_count() >= self.max_members
    
    def can_join(self, user):
        return not self.is_full() and user not in self.members.all()
    
    def can_leave(self, user):
        return user in self.members.all() and user != self.created_by

class GroupMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('file', 'File'),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    media_file = models.FileField(upload_to='group_media/', null=True, blank=True)
    media_thumbnail = models.ImageField(upload_to='group_media/thumbnails/', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.group.name} - {self.user.username} - {self.timestamp}"
    
    def get_file_name(self):
        """Get the original filename of the media"""
        if self.media_file:
            return self.media_file.name.split('/')[-1]
        return None
    
    def get_file_size(self):
        """Get the file size in human readable format"""
        if self.media_file:
            size = self.media_file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return None
    
    def is_image(self):
        """Check if the message contains an image"""
        if self.media_file:
            ext = self.media_file.name.split('.')[-1].lower()
            return ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return False
    
    def is_video(self):
        """Check if the message contains a video"""
        if self.media_file:
            ext = self.media_file.name.split('.')[-1].lower()
            return ext in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
        return False

class LearningTrack(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    progress = models.IntegerField(default=0)  # Progress percentage
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title

class UploadedFile(models.Model):
    FILE_TYPES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.original_name} - {self.user.username}"
    
    def get_file_extension(self):
        """Get the file extension"""
        return self.original_name.split('.')[-1].lower() if '.' in self.original_name else ''

class Folder(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['name', 'user', 'parent_folder']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def get_full_path(self):
        """Get the full path of the folder including parent folders"""
        path = [self.name]
        current = self.parent_folder
        while current:
            path.insert(0, current.name)
            current = current.parent_folder
        return ' / '.join(path)
    
    def get_file_count(self):
        """Get the total number of files in this folder (including subfolders)"""
        count = self.files.count()
        for subfolder in self.subfolders.all():
            count += subfolder.get_file_count()
        return count
    
    def get_folder_count(self):
        """Get the total number of subfolders"""
        return self.subfolders.count()

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Chat - {self.user.username} - {self.timestamp}"

class Connection(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_connections')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_connections')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, help_text="Connection request message")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['sender', 'receiver']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"
    
    @classmethod
    def are_connected(cls, user1, user2):
        """Check if two users are connected"""
        return cls.objects.filter(
            (models.Q(sender=user1, receiver=user2) | models.Q(sender=user2, receiver=user1)),
            status='accepted'
        ).exists()
    
    @classmethod
    def get_connection_status(cls, user1, user2):
        """Get the connection status between two users"""
        connection = cls.objects.filter(
            (models.Q(sender=user1, receiver=user2) | models.Q(sender=user2, receiver=user1))
        ).first()
        
        if not connection:
            return 'none'
        elif connection.status == 'pending':
            return 'pending_sent' if connection.sender == user1 else 'pending_received'
        else:
            return connection.status

class DirectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.message[:50]}"

class VideoCallSession(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_calls')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participated_calls')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_time = models.DateTimeField()
    duration = models.IntegerField(default=30, help_text="Duration in minutes")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='scheduled')
    room_id = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-scheduled_time']
    
    def __str__(self):
        return f"{self.title} - {self.initiator.username} & {self.participant.username}"
    
    def generate_room_id(self):
        """Generate a unique room ID for the video call"""
        import uuid
        return str(uuid.uuid4())

class GroupJoinRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_join_requests')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, help_text="Optional message to the group owner")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'group']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} -> {self.group.name} ({self.status})"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
