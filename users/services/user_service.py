from users.repository.user_repository import UserRepository
from users.dto.user_dto import UserDTO, UserUpdateDTO
from dataclasses import asdict

class UserService:
    def __init__(self, user_repository: UserRepository = None):
        self.user_repository = user_repository or UserRepository()

    def get_profile(self, user_id: int) -> UserDTO | None:
        return self.user_repository.get_by_id(user_id)

    def update_profile(self, user_id: int, update_dto: UserUpdateDTO) -> UserDTO | None:
        update_data = asdict(update_dto)
        return self.user_repository.update(user_id, update_data)

    def get_online_users(self) -> list[UserDTO]:
        return self.user_repository.get_online_users()

    def get_subscription(self, user_id: int) -> str | None:
        user = self.user_repository.get_by_id(user_id)
        if user:
            return user.subscription_type
        return None
