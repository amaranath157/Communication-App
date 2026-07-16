from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from common.utils import success_response, error_response
from users.services.user_service import UserService
from users.serializers.user_serializer import UserUpdateSerializer
from users.dto.user_dto import UserUpdateDTO
from dataclasses import asdict

class ProfileController(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_service = UserService()

    def get(self, request):
        user_dto = self.user_service.get_profile(request.user.id)
        if not user_dto:
            return error_response(message="User not found", status_code=404)
        return success_response(data=asdict(user_dto), message="Profile fetched successfully")

    def put(self, request):
        serializer = UserUpdateSerializer(data=request.data)
        if serializer.is_valid():
            update_dto = UserUpdateDTO(**serializer.validated_data)
            updated_user = self.user_service.update_profile(request.user.id, update_dto)
            if not updated_user:
                return error_response(message="User not found", status_code=404)
            return success_response(data=asdict(updated_user), message="Profile updated successfully")
        return error_response(message="Validation failed", errors=serializer.errors)

class OnlineUsersController(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_service = UserService()

    def get(self, request):
        online_users = self.user_service.get_online_users()
        data = [asdict(user) for user in online_users]
        return success_response(data=data, message="Online users fetched successfully")

class SubscriptionController(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_service = UserService()

    def get(self, request):
        subscription = self.user_service.get_subscription(request.user.id)
        if not subscription:
            return error_response(message="User not found", status_code=404)
        return success_response(data={"subscription_type": subscription}, message="Subscription fetched successfully")
