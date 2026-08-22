from .models import Notification

class NotificationService:
    @staticmethod
    def create_notification(user, title, message, type='ALERT', link_url=''):
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            type=type,
            link_url=link_url
        )
