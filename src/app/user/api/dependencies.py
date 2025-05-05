from src.app.user.model.group import GroupInvitation
from src.app.user.model.user_data import UserBusinessData, UserData
from src.app.user.model.wakapi import Users
from src.app.user.repository.group import GroupInvitationRepository
from src.app.user.repository.user_data import UserBusinessDataRepository, UserDataRepository
from src.app.user.repository.wakapi import WakapiUserRepository
from src.app.user.service.group import GroupService
from src.app.user.service.user_data import UserDataService
from src.app.user.service.wakapi import WakapiService
from src.core.dependencies.auth import keycloak_admin

invitation_repository = GroupInvitationRepository(GroupInvitation)
group_service = GroupService(invitation_repository, keycloak_admin)

user_data_repository = UserDataRepository(UserData)
user_business_data_repository = UserBusinessDataRepository(UserBusinessData)
user_data_service = UserDataService(user_data_repository, user_business_data_repository, keycloak_admin)

wakapi_repository = WakapiUserRepository(Users)
wakapi_service = WakapiService(wakapi_repository)
