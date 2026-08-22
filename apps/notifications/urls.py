from django.urls import path
from .views import NotificationListView, MarkNotificationReadView, MarkAllNotificationsReadView

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', MarkAllNotificationsReadView.as_view(), name='notification-read-all'),
]
