from django.contrib import admin
from .models import UserProfile, Group, LearningTrack, UploadedFile, ChatMessage, GroupMessage, Connection, DirectMessage, VideoCallSession, Folder

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'skills', 'education', 'interests']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'skills', 'interests']
    list_filter = ['education']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'privacy', 'member_count', 'max_members', 'is_active', 'invite_enabled', 'created_at']
    list_filter = ['privacy', 'is_active', 'invite_enabled', 'created_at']
    search_fields = ['name', 'description', 'created_by__username', 'invite_code']
    readonly_fields = ['member_count', 'invite_code']

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'

@admin.register(LearningTrack)
class LearningTrackAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'progress', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'user__username']

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'user', 'folder', 'file_type', 'file_size', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at', 'folder']
    search_fields = ['original_name', 'user__username', 'description']
    readonly_fields = ['file_size']

@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'parent_folder', 'file_count', 'folder_count', 'created_at']
    list_filter = ['created_at', 'parent_folder']
    search_fields = ['name', 'user__username']
    readonly_fields = ['file_count', 'folder_count']

    def file_count(self, obj):
        return obj.get_file_count()
    file_count.short_description = 'Files'

    def folder_count(self, obj):
        return obj.get_folder_count()
    folder_count.short_description = 'Subfolders'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'response', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__username', 'message', 'response']

@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'message_type', 'message', 'timestamp']
    list_filter = ['message_type', 'timestamp', 'group']
    search_fields = ['message', 'user__username', 'group__name']
    readonly_fields = ['get_file_name', 'get_file_size']

@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__username', 'receiver__username', 'message']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'message', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['message', 'sender__username', 'receiver__username']

@admin.register(VideoCallSession)
class VideoCallSessionAdmin(admin.ModelAdmin):
    list_display = ['initiator', 'participant', 'status', 'scheduled_time', 'created_at']
    list_filter = ['status', 'created_at', 'scheduled_time']
    search_fields = ['initiator__username', 'participant__username', 'title']
