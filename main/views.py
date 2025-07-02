from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
import json
import os
import google.generativeai as genai
from .forms import SignUpForm, UserProfileForm, GroupForm, LearningTrackForm, FileUploadForm, GroupMessageForm, GroupSearchForm, ConnectionRequestForm, DirectMessageForm, VideoCallForm, UserSearchForm, FolderForm
from .models import UserProfile, Group, LearningTrack, UploadedFile, ChatMessage, GroupMessage, Connection, DirectMessage, VideoCallSession, Folder, GroupJoinRequest

def get_unread_messages_count(request):
    """Context processor to get unread messages count for sidebar"""
    if request.user.is_authenticated:
        # Get unread messages from connections only
        unread_count = DirectMessage.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        return {'unread_messages_count': unread_count}
    return {'unread_messages_count': 0}

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def home(request):
    # Get user statistics
    user_groups = Group.objects.filter(members=request.user).count()
    user_tracks = LearningTrack.objects.filter(user=request.user).count()
    user_files = UploadedFile.objects.filter(user=request.user).count()
    
    # Get recent activity
    recent_groups = Group.objects.filter(members=request.user).order_by('-created_at')[:3]
    recent_files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')[:5]
    recent_tracks = LearningTrack.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    # Get connections count
    connections_count = Connection.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)) & 
        Q(status='accepted')
    ).count()
    
    # Get pending join requests count
    pending_requests = GroupJoinRequest.objects.filter(
        user=request.user, 
        status='pending'
    ).count()
    
    # Get upcoming video calls
    upcoming_calls = VideoCallSession.objects.filter(
        (Q(initiator=request.user) | Q(participant=request.user)) &
        Q(status='scheduled') &
        Q(scheduled_time__gte=timezone.now())
    ).order_by('scheduled_time')[:3]
    
    context = {
        'user_groups': user_groups,
        'user_tracks': user_tracks,
        'user_files': user_files,
        'connections_count': connections_count,
        'pending_requests': pending_requests,
        'recent_groups': recent_groups,
        'recent_files': recent_files,
        'recent_tracks': recent_tracks,
        'upcoming_calls': upcoming_calls,
    }
    return render(request, 'main/home.html', context)

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'main/profile.html', {'form': form, 'profile': profile})

@login_required
def user_settings(request):
    return render(request, 'main/settings.html')

@login_required
def groups(request):
    user_groups = Group.objects.filter(members=request.user)
    all_groups = Group.objects.exclude(members=request.user)
    
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.privacy = request.POST.get('privacy', 'public')
            group.max_members = int(request.POST.get('max_members', 50))
            group.save()
            group.members.add(request.user)
            messages.success(request, 'Group created successfully!')
            return redirect('groups')
    else:
        form = GroupForm()
    
    context = {
        'user_groups': user_groups,
        'all_groups': all_groups,
        'form': form,
    }
    return render(request, 'main/groups.html', context)

@login_required
def join_group(request, group_id):
    """Join a group or send join request for private groups"""
    group = get_object_or_404(Group, id=group_id, is_active=True)
    
    # Check if user is already a member
    if request.user in group.members.all():
        messages.error(request, f'You are already a member of {group.name}!')
        return redirect('group_detail', group_id=group.id)
    
    # Check if group is full
    if group.is_full():
        messages.error(request, f'{group.name} is full!')
        return redirect('group_detail', group_id=group.id)
    
    # Handle private groups with join requests
    if group.privacy == 'private':
        # Check if there's already a pending request
        existing_request = GroupJoinRequest.objects.filter(
            user=request.user, 
            group=group, 
            status='pending'
        ).first()
        
        if existing_request:
            messages.info(request, f'You already have a pending join request for {group.name}.')
            return redirect('group_detail', group_id=group.id)
        
        # Create join request
        message = request.POST.get('message', '')
        GroupJoinRequest.objects.create(
            user=request.user,
            group=group,
            message=message
        )
        messages.success(request, f'Join request sent to {group.name}! The group owner will review your request.')
        return redirect('group_detail', group_id=group.id)
    
    # Handle public groups (direct join)
    else:
        group.members.add(request.user)
        messages.success(request, f'You joined {group.name}!')
        return redirect('group_detail', group_id=group.id)

@login_required
def chatbot(request):
    chat_history = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:10]
    return render(request, 'main/chatbot.html', {'chat_history': chat_history})

@csrf_exempt
@login_required
def chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            if not user_message:
                return JsonResponse({'error': 'No message provided'}, status=400)
            
            # Configure Gemini API
            api_key = getattr(settings, 'GEMINI_API_KEY', '')
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    
                    # Try gemini-1.5-flash first (more efficient), fallback to gemini-1.5-pro
                    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
                    bot_response = None
                    
                    for model_name in models_to_try:
                        try:
                            model = genai.GenerativeModel(model_name)
                            
                            # Create a context-aware prompt for study assistance
                            system_prompt = f"""You are StudPro AI Assistant, an intelligent study companion designed to help students with their academic needs. 

Your role is to:
- Provide helpful study tips and techniques
- Assist with homework and assignments
- Explain complex concepts in simple terms
- Offer learning strategies and time management advice
- Help with research and academic writing
- Answer general knowledge questions
- Be encouraging and supportive

User: {request.user.first_name} {request.user.last_name}
Current message: {user_message}

Please provide a helpful, educational, and encouraging response. Keep responses concise but informative (2-4 sentences typically). If the user asks about something outside your expertise, politely redirect them to appropriate resources."""
                            
                            # Generate response with context
                            response = model.generate_content(system_prompt)
                            bot_response = response.text
                            
                            # Clean up the response if it contains markdown or formatting
                            bot_response = bot_response.replace('**', '').replace('*', '').replace('`', '')
                            
                            # If we get here, the model worked, so break out of the loop
                            break
                            
                        except Exception as model_error:
                            print(f"Model {model_name} failed: {str(model_error)}")
                            continue
                    
                    # If all models failed, provide a fallback response
                    if not bot_response:
                        bot_response = "I'm having trouble connecting to the AI service right now. Please try again in a moment or contact support if the issue persists."
                    
                except Exception as genai_error:
                    print(f"Gemini API Error: {str(genai_error)}")
                    
                    # Check for specific quota errors
                    error_str = str(genai_error).lower()
                    if 'quota' in error_str or '429' in error_str:
                        bot_response = "I've reached my daily usage limit. Please try again tomorrow or upgrade your plan for unlimited access. In the meantime, you can explore our study resources and connect with other students!"
                    elif 'api key' in error_str or 'authentication' in error_str:
                        bot_response = "There's an issue with the AI service authentication. Please check your API configuration or contact support."
                    elif 'network' in error_str or 'connection' in error_str:
                        bot_response = "I'm having trouble connecting to the AI service. Please check your internet connection and try again."
                    else:
                        bot_response = "I encountered an unexpected error. Please try again in a moment or contact support if the issue persists."
            else:
                bot_response = "I'm sorry, but the AI service is currently unavailable. Please check your API configuration or try again later."
            
            # Save chat message
            ChatMessage.objects.create(
                user=request.user,
                message=user_message,
                response=bot_response
            )
            
            return JsonResponse({'response': bot_response})
            
        except Exception as e:
            # Log the error for debugging
            print(f"Chat API Error: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            
            # Provide user-friendly error message
            error_message = "I encountered an unexpected error. Please try again in a moment or contact support if the issue persists."
            
            return JsonResponse({'error': error_message}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def learning_track(request):
    tracks = LearningTrack.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = LearningTrackForm(request.POST)
        if form.is_valid():
            track = form.save(commit=False)
            track.user = request.user
            track.save()
            messages.success(request, 'Learning track created successfully!')
            return redirect('learning_track')
    else:
        form = LearningTrackForm()
    
    context = {
        'tracks': tracks,
        'form': form,
    }
    return render(request, 'main/learning_track.html', context)

@login_required
def update_progress(request, track_id):
    if request.method == 'POST':
        track = get_object_or_404(LearningTrack, id=track_id, user=request.user)
        progress = int(request.POST.get('progress', 0))
        track.progress = min(100, max(0, progress))
        if track.progress == 100:
            track.completed = True
        track.save()
        messages.success(request, 'Progress updated!')
    return redirect('learning_track')

@login_required
def files(request, folder_id=None):
    """View files and folders"""
    current_folder = None
    if folder_id:
        current_folder = get_object_or_404(Folder, id=folder_id, user=request.user)
    
    # Get folders and files in current folder
    folders = Folder.objects.filter(user=request.user, parent_folder=current_folder)
    files_list = UploadedFile.objects.filter(user=request.user, folder=current_folder)
    
    # Get breadcrumb navigation
    breadcrumbs = []
    if current_folder:
        breadcrumbs = current_folder.get_full_path().split(' / ')
    
    if request.method == 'POST':
        if 'upload_file' in request.POST:
            form = FileUploadForm(request.POST, request.FILES, user=request.user, current_folder=current_folder)
            if form.is_valid():
                file_obj = form.save(commit=False)
                file_obj.user = request.user
                file_obj.original_name = request.FILES['file'].name
                file_obj.file_type = get_file_type(request.FILES['file'].name)
                file_obj.file_size = request.FILES['file'].size
                
                # Set the folder from the form data or current folder
                if form.cleaned_data.get('folder'):
                    file_obj.folder = form.cleaned_data['folder']
                elif current_folder:
                    file_obj.folder = current_folder
                
                file_obj.save()
                messages.success(request, 'File uploaded successfully!')
                if folder_id:
                    return redirect('files', folder_id=folder_id)
                else:
                    return redirect('files')
        elif 'create_folder' in request.POST:
            folder_form = FolderForm(request.POST, user=request.user, parent_folder=current_folder)
            if folder_form.is_valid():
                folder = folder_form.save(commit=False)
                folder.user = request.user
                folder.save()
                messages.success(request, f'Folder "{folder.name}" created successfully!')
                if folder_id:
                    return redirect('files', folder_id=folder_id)
                else:
                    return redirect('files')
    else:
        form = FileUploadForm(user=request.user, current_folder=current_folder)
        folder_form = FolderForm(user=request.user, parent_folder=current_folder)
    
    context = {
        'folders': folders,
        'files': files_list,
        'current_folder': current_folder,
        'breadcrumbs': breadcrumbs,
        'form': form,
        'folder_form': folder_form,
    }
    return render(request, 'main/files.html', context)

@login_required
def create_folder(request, parent_folder_id=None):
    """Create a new folder"""
    parent_folder = None
    if parent_folder_id:
        parent_folder = get_object_or_404(Folder, id=parent_folder_id, user=request.user)
    
    if request.method == 'POST':
        form = FolderForm(request.POST, user=request.user, parent_folder=parent_folder)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.user = request.user
            folder.save()
            messages.success(request, f'Folder "{folder.name}" created successfully!')
            if parent_folder:
                return redirect('files', folder_id=parent_folder.id)
            else:
                return redirect('files')
    else:
        form = FolderForm(user=request.user, parent_folder=parent_folder)
    
    context = {
        'form': form,
        'parent_folder': parent_folder,
    }
    return render(request, 'main/create_folder.html', context)

@login_required
def delete_folder(request, folder_id):
    """Delete a folder and all its contents"""
    folder = get_object_or_404(Folder, id=folder_id, user=request.user)
    
    if request.method == 'POST':
        folder_name = folder.name
        parent_folder_id = folder.parent_folder.id if folder.parent_folder else None
        
        # Delete the folder (this will cascade delete all files and subfolders)
        folder.delete()
        messages.success(request, f'Folder "{folder_name}" and all its contents deleted successfully!')
        if parent_folder_id:
            return redirect('files', folder_id=parent_folder_id)
        else:
            return redirect('files')
    
    context = {
        'folder': folder,
    }
    return render(request, 'main/delete_folder.html', context)

def get_file_type(filename):
    """Determine file type based on extension"""
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    document_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']
    video_extensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv']
    
    if ext in document_extensions:
        return 'document'
    elif ext in image_extensions:
        return 'image'
    elif ext in video_extensions:
        return 'video'
    else:
        return 'other'

@login_required
def delete_file(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    folder_id = file_obj.folder.id if file_obj.folder else None
    file_obj.file.delete()
    file_obj.delete()
    messages.success(request, 'File deleted successfully!')
    if folder_id:
        return redirect('files', folder_id=folder_id)
    else:
        return redirect('files')

@login_required
def explore_groups(request):
    """Explore and search for groups to join"""
    form = GroupSearchForm(request.GET)
    groups = Group.objects.filter(is_active=True)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        privacy = form.cleaned_data.get('privacy')
        
        if search:
            groups = groups.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        if privacy:
            groups = groups.filter(privacy=privacy)
    
    # Exclude groups the user is already a member of
    groups = groups.exclude(members=request.user)
    
    context = {
        'groups': groups,
        'form': form,
    }
    return render(request, 'main/explore_groups.html', context)

@login_required
def group_detail(request, group_id):
    """View group details and messages"""
    group = get_object_or_404(Group, id=group_id, is_active=True)
    messages_list = group.messages.all()[:50]  # Get last 50 messages
    is_member = request.user in group.members.all()
    
    # Check if user has a pending join request
    has_pending_request = False
    if not is_member and group.privacy == 'private':
        has_pending_request = GroupJoinRequest.objects.filter(
            user=request.user, 
            group=group, 
            status='pending'
        ).exists()
    
    # Get pending requests count for group owner
    pending_requests_count = 0
    if group.created_by == request.user and group.privacy == 'private':
        pending_requests_count = GroupJoinRequest.objects.filter(
            group=group, 
            status='pending'
        ).count()
    
    if request.method == 'POST' and is_member:
        form = GroupMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.group = group
            message.user = request.user
            message.save()
            messages.success(request, 'Message sent!')
            return redirect('group_detail', group_id=group.id)
    else:
        form = GroupMessageForm()
    
    context = {
        'group': group,
        'messages': messages_list,
        'form': form,
        'is_member': is_member,
        'has_pending_request': has_pending_request,
        'pending_requests_count': pending_requests_count,
    }
    return render(request, 'main/group_detail.html', context)

@login_required
def leave_group(request, group_id):
    """Leave a group"""
    group = get_object_or_404(Group, id=group_id)
    
    if group.can_leave(request.user):
        group.members.remove(request.user)
        messages.success(request, f'You left {group.name}!')
        return redirect('explore_groups')
    else:
        messages.error(request, 'You cannot leave this group!')
        return redirect('group_detail', group_id=group.id)

@login_required
def my_groups(request):
    """View user's joined groups"""
    user_groups = Group.objects.filter(members=request.user, is_active=True)
    created_groups = Group.objects.filter(created_by=request.user, is_active=True)
    
    context = {
        'user_groups': user_groups,
        'created_groups': created_groups,
    }
    return render(request, 'main/my_groups.html', context)

@login_required
def networking(request):
    """Main networking page - discover and connect with users"""
    form = UserSearchForm(request.GET)
    users = User.objects.exclude(id=request.user.id)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        skills = form.cleaned_data.get('skills')
        
        if search:
            users = users.filter(
                Q(first_name__icontains=search) | 
                Q(last_name__icontains=search) | 
                Q(username__icontains=search) |
                Q(userprofile__skills__icontains=search) |
                Q(userprofile__interests__icontains=search)
            )
        
        if skills:
            users = users.filter(userprofile__skills__icontains=skills)
    
    # Get connection status for each user
    for user in users:
        user.connection_status = Connection.get_connection_status(request.user, user)
        user.is_connected = Connection.are_connected(request.user, user)
    
    context = {
        'users': users,
        'form': form,
    }
    return render(request, 'main/networking.html', context)

@login_required
def user_profile_view(request, user_id):
    """View another user's profile"""
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Check connection status
    connection_status = Connection.get_connection_status(request.user, user)
    is_connected = Connection.are_connected(request.user, user)
    
    # Get recent messages if connected
    recent_messages = []
    if is_connected:
        recent_messages = DirectMessage.objects.filter(
            (Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user))
        ).order_by('-timestamp')[:5]
    
    context = {
        'profile_user': user,
        'profile': profile,
        'connection_status': connection_status,
        'is_connected': is_connected,
        'recent_messages': recent_messages,
    }
    return render(request, 'main/user_profile.html', context)

@login_required
def send_connection_request(request, user_id):
    """Send a connection request"""
    receiver = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = ConnectionRequestForm(request.POST)
        if form.is_valid():
            # Check if connection already exists
            existing_connection = Connection.objects.filter(
                (Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user))
            ).first()
            
            if existing_connection:
                messages.error(request, 'Connection request already exists!')
            else:
                connection = form.save(commit=False)
                connection.sender = request.user
                connection.receiver = receiver
                connection.save()
                messages.success(request, f'Connection request sent to {receiver.first_name}!')
    else:
        form = ConnectionRequestForm()
    
    return redirect('user_profile', user_id=user_id)

@login_required
def accept_connection(request, connection_id):
    """Accept a connection request"""
    connection = get_object_or_404(Connection, id=connection_id, receiver=request.user, status='pending')
    connection.status = 'accepted'
    connection.save()
    messages.success(request, f'You are now connected with {connection.sender.first_name}!')
    return redirect('connections')

@login_required
def reject_connection(request, connection_id):
    """Reject a connection request"""
    connection = get_object_or_404(Connection, id=connection_id, receiver=request.user, status='pending')
    connection.status = 'rejected'
    connection.save()
    messages.success(request, f'Connection request from {connection.sender.first_name} rejected.')
    return redirect('connections')

@login_required
def connections(request):
    """View all connections and pending requests"""
    # Get accepted connections
    accepted_connections = Connection.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)),
        status='accepted'
    )
    
    # Get pending requests received
    pending_received = Connection.objects.filter(receiver=request.user, status='pending')
    
    # Get pending requests sent
    pending_sent = Connection.objects.filter(sender=request.user, status='pending')
    
    context = {
        'accepted_connections': accepted_connections,
        'pending_received': pending_received,
        'pending_sent': pending_sent,
    }
    return render(request, 'main/connections.html', context)

@login_required
def messages_list(request):
    """List of all conversations"""
    # Get all messages involving the user, newest first
    messages = DirectMessage.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-timestamp')

    unique_user_ids = set()
    conversations = []

    for msg in messages:
        # Identify the other user in the conversation
        other_user = msg.receiver if msg.sender == request.user else msg.sender
        if other_user.id == request.user.id or other_user.id in unique_user_ids:
            continue  # Skip self and already added users
        unique_user_ids.add(other_user.id)

        # Get unread count
        unread_count = DirectMessage.objects.filter(
            sender=other_user, receiver=request.user, is_read=False
        ).count()

        conversations.append({
            'user': other_user,
            'last_message': msg,  # msg is already the latest for this pair
            'unread_count': unread_count,
            'is_connected': Connection.are_connected(request.user, other_user)
        })

    context = {
        'conversations': conversations,
    }
    return render(request, 'main/messages_list.html', context)

@login_required
def direct_message(request, user_id):
    """Direct messaging with a specific user"""
    other_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = DirectMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = other_user
            message.save()
            return redirect('direct_message', user_id=user_id)
    else:
        form = DirectMessageForm()
    
    # Get all messages between users
    messages_list = DirectMessage.objects.filter(
        (Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user))
    ).order_by('timestamp')
    
    # Mark messages as read
    DirectMessage.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    context = {
        'other_user': other_user,
        'messages': messages_list,
        'form': form,
        'is_connected': Connection.are_connected(request.user, other_user)
    }
    return render(request, 'main/direct_message.html', context)

@login_required
def video_calls(request):
    """View and manage video calls"""
    # Get scheduled calls
    scheduled_calls = VideoCallSession.objects.filter(
        (Q(initiator=request.user) | Q(participant=request.user)),
        status='scheduled'
    )
    
    # Get completed calls
    completed_calls = VideoCallSession.objects.filter(
        (Q(initiator=request.user) | Q(participant=request.user)),
        status='completed'
    )
    
    context = {
        'scheduled_calls': scheduled_calls,
        'completed_calls': completed_calls,
    }
    return render(request, 'main/video_calls.html', context)

@login_required
def schedule_video_call(request, user_id):
    """Schedule a video call with a user"""
    participant = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = VideoCallForm(request.POST)
        if form.is_valid():
            call = form.save(commit=False)
            call.initiator = request.user
            call.participant = participant
            call.room_id = call.generate_room_id()
            call.save()
            messages.success(request, f'Video call scheduled with {participant.first_name}!')
            return redirect('video_calls')
    else:
        form = VideoCallForm()
    
    context = {
        'participant': participant,
        'form': form,
    }
    return render(request, 'main/schedule_video_call.html', context)

@login_required
def video_call_room(request, call_id):
    """Join a video call room"""
    call = get_object_or_404(VideoCallSession, id=call_id)
    
    # Check if user is part of the call
    if call.initiator != request.user and call.participant != request.user:
        messages.error(request, 'You are not authorized to join this call.')
        return redirect('video_calls')
    
    # Update call status if starting
    if call.status == 'scheduled':
        call.status = 'ongoing'
        call.started_at = timezone.now()
        call.save()
    
    context = {
        'call': call,
        'room_id': call.room_id,
        'is_initiator': call.initiator == request.user,
    }
    return render(request, 'main/video_call_room.html', context)

@login_required
def end_video_call(request, call_id):
    """End a video call"""
    call = get_object_or_404(VideoCallSession, id=call_id)
    
    if call.initiator == request.user or call.participant == request.user:
        call.status = 'completed'
        call.ended_at = timezone.now()
        call.save()
        messages.success(request, 'Video call ended.')
    
    return redirect('video_calls')

@login_required
def join_group_invite(request, invite_code):
    """Join a group using an invite link"""
    group = get_object_or_404(Group, invite_code=invite_code, is_active=True)
    
    # Check if invite is valid
    if not group.is_invite_valid():
        messages.error(request, 'This invite link has expired or is disabled.')
        return redirect('explore_groups')
    
    # Check if user can join
    if group.can_join(request.user):
        group.members.add(request.user)
        messages.success(request, f'You joined {group.name} using the invite link!')
        return redirect('group_detail', group_id=group.id)
    else:
        if group.is_full():
            messages.error(request, f'{group.name} is full!')
        else:
            messages.error(request, f'You are already a member of {group.name}!')
        return redirect('group_detail', group_id=group.id)

@login_required
def manage_group_invite(request, group_id):
    """Manage group invite links"""
    group = get_object_or_404(Group, id=group_id, created_by=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_invite':
            expires_days = int(request.POST.get('expires_days', 7))
            invite_link = group.create_invite_link(expires_days)
            messages.success(request, f'New invite link created! Expires in {expires_days} days.')
        
        elif action == 'disable_invite':
            group.disable_invite_link()
            messages.success(request, 'Invite link disabled.')
        
        elif action == 'regenerate_invite':
            expires_days = int(request.POST.get('expires_days', 7))
            invite_link = group.create_invite_link(expires_days)
            messages.success(request, f'New invite link generated! Expires in {expires_days} days.')
    
    context = {
        'group': group,
    }
    return render(request, 'main/manage_group_invite.html', context)

@login_required
def manage_join_requests(request, group_id):
    """View and manage join requests for a group"""
    group = get_object_or_404(Group, id=group_id, created_by=request.user)
    
    # Get pending join requests
    pending_requests = GroupJoinRequest.objects.filter(
        group=group, 
        status='pending'
    ).select_related('user')
    
    # Get recent processed requests
    processed_requests = GroupJoinRequest.objects.filter(
        group=group, 
        status__in=['approved', 'rejected']
    ).select_related('user').order_by('-updated_at')[:10]
    
    context = {
        'group': group,
        'pending_requests': pending_requests,
        'processed_requests': processed_requests,
    }
    return render(request, 'main/manage_join_requests.html', context)

@login_required
def approve_join_request(request, request_id):
    """Approve a join request"""
    join_request = get_object_or_404(GroupJoinRequest, id=request_id)
    group = join_request.group
    
    # Check if user is the group owner
    if group.created_by != request.user:
        messages.error(request, 'You are not authorized to approve join requests for this group.')
        return redirect('group_detail', group_id=group.id)
    
    # Check if group is full
    if group.is_full():
        messages.error(request, f'{group.name} is full! Cannot approve more join requests.')
        return redirect('manage_join_requests', group_id=group.id)
    
    # Approve the request
    join_request.status = 'approved'
    join_request.save()
    
    # Add user to group
    group.members.add(join_request.user)
    
    messages.success(request, f'Approved {join_request.user.username}\'s join request for {group.name}!')
    return redirect('manage_join_requests', group_id=group.id)

@login_required
def reject_join_request(request, request_id):
    """Reject a join request"""
    join_request = get_object_or_404(GroupJoinRequest, id=request_id)
    group = join_request.group
    
    # Check if user is the group owner
    if group.created_by != request.user:
        messages.error(request, 'You are not authorized to reject join requests for this group.')
        return redirect('group_detail', group_id=group.id)
    
    # Reject the request
    join_request.status = 'rejected'
    join_request.save()
    
    messages.success(request, f'Rejected {join_request.user.username}\'s join request for {group.name}.')
    return redirect('manage_join_requests', group_id=group.id)

@login_required
def my_join_requests(request):
    """View user's own join requests"""
    # Get user's pending join requests
    pending_requests = GroupJoinRequest.objects.filter(
        user=request.user, 
        status='pending'
    ).select_related('group', 'group__created_by')
    
    # Get user's processed join requests
    processed_requests = GroupJoinRequest.objects.filter(
        user=request.user, 
        status__in=['approved', 'rejected']
    ).select_related('group', 'group__created_by').order_by('-updated_at')
    
    context = {
        'pending_requests': pending_requests,
        'processed_requests': processed_requests,
    }
    return render(request, 'main/my_join_requests.html', context)
