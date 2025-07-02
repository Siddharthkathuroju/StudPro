from .models import DirectMessage

def unread_messages_count(request):
    """Context processor to get unread messages count for sidebar"""
    if request.user.is_authenticated:
        # Get unread messages from connections only
        unread_count = DirectMessage.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        return {'unread_messages_count': unread_count}
    return {'unread_messages_count': 0} 