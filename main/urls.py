from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signin/', auth_views.LoginView.as_view(), name='signin'),
    path('signout/', auth_views.LogoutView.as_view(), name='signout'),
    
    # Main app URLs
    path('profile/', views.profile, name='profile'),
    path('settings/', views.user_settings, name='settings'),
    path('groups/', views.groups, name='groups'),
    path('join-group/<int:group_id>/', views.join_group, name='join_group'),
    path('explore-groups/', views.explore_groups, name='explore_groups'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('leave-group/<int:group_id>/', views.leave_group, name='leave_group'),
    path('my-groups/', views.my_groups, name='my_groups'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chat-api/', views.chat_api, name='chat_api'),
    path('learning-track/', views.learning_track, name='learning_track'),
    path('update-progress/<int:track_id>/', views.update_progress, name='update_progress'),
    path('files/', views.files, name='files'),
    path('files/folder/<int:folder_id>/', views.files, name='files'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('create-folder/<int:parent_folder_id>/', views.create_folder, name='create_folder'),
    path('delete-folder/<int:folder_id>/', views.delete_folder, name='delete_folder'),
    path('delete-file/<int:file_id>/', views.delete_file, name='delete_file'),
    
    # Networking URLs
    path('networking/', views.networking, name='networking'),
    path('user/<int:user_id>/', views.user_profile_view, name='user_profile'),
    path('send-connection/<int:user_id>/', views.send_connection_request, name='send_connection'),
    path('accept-connection/<int:connection_id>/', views.accept_connection, name='accept_connection'),
    path('reject-connection/<int:connection_id>/', views.reject_connection, name='reject_connection'),
    path('connections/', views.connections, name='connections'),
    path('messages/', views.messages_list, name='messages_list'),
    path('message/<int:user_id>/', views.direct_message, name='direct_message'),
    path('video-calls/', views.video_calls, name='video_calls'),
    path('schedule-call/<int:user_id>/', views.schedule_video_call, name='schedule_video_call'),
    path('video-call/<int:call_id>/', views.video_call_room, name='video_call_room'),
    path('end-call/<int:call_id>/', views.end_video_call, name='end_video_call'),
    path('join-group-invite/<str:invite_code>/', views.join_group_invite, name='join_group_invite'),
    path('manage-group-invite/<int:group_id>/', views.manage_group_invite, name='manage_group_invite'),
    
    # Join Request Management URLs
    path('manage-join-requests/<int:group_id>/', views.manage_join_requests, name='manage_join_requests'),
    path('approve-join-request/<int:request_id>/', views.approve_join_request, name='approve_join_request'),
    path('reject-join-request/<int:request_id>/', views.reject_join_request, name='reject_join_request'),
    path('my-join-requests/', views.my_join_requests, name='my_join_requests'),
]
