from django.urls import path
from .views import PublicRentalAgentView, PrivateRentalAgentView

urlpatterns = [
    path("assistant/public/", PublicRentalAgentView.as_view(), name="assistant-public"),
    path("assistant/private/", PrivateRentalAgentView.as_view(), name="assistant-private"),
]