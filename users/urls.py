from django.urls import path
from users.controllers.user_controller import ProfileController, OnlineUsersController, SubscriptionController

urlpatterns = [
    path('profile/', ProfileController.as_view(), name='user-profile'),
    path('online-users/', OnlineUsersController.as_view(), name='online-users'),
    path('subscription/', SubscriptionController.as_view(), name='user-subscription'),
]
