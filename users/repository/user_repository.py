from users.models import User
from users.dto.user_dto import UserDTO
from django.core.exceptions import ObjectDoesNotExist

class UserRepository:
    @staticmethod
    def _map_to_dto(user: User) -> UserDTO:
        return UserDTO(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            gender=user.gender,
            age=user.age,
            bio=user.bio,
            country=user.country,
            profile_photo=user.profile_photo,
            is_online=user.is_online,
            subscription_type=user.subscription_type
        )

    def get_by_id(self, user_id: int) -> UserDTO | None:
        try:
            user = User.objects.get(id=user_id)
            return self._map_to_dto(user)
        except ObjectDoesNotExist:
            return None

    def get_by_email(self, email: str) -> UserDTO | None:
        try:
            user = User.objects.get(email=email)
            return self._map_to_dto(user)
        except ObjectDoesNotExist:
            return None

    def update(self, user_id: int, update_data: dict) -> UserDTO | None:
        try:
            # Filter out None values to not overwrite existing data with None unnecessarily
            cleaned_data = {k: v for k, v in update_data.items() if v is not None}
            User.objects.filter(id=user_id).update(**cleaned_data)
            updated_user = User.objects.get(id=user_id)
            return self._map_to_dto(updated_user)
        except ObjectDoesNotExist:
            return None

    def get_online_users(self) -> list[UserDTO]:
        users = User.objects.filter(is_online=True)
        return [self._map_to_dto(user) for user in users]
