from src.app.user.model.user_data import UserBusinessData, UserData
from src.app.user.model.wakapi import Users
from src.app.user.repository.user_data import UserBusinessData, UserBusinessDataRepository, UserDataRepository
from src.app.user.repository.wakapi import WakapiUserRepository
from src.app.user.service.user_data import UserDataService
from src.app.user.service.wakapi import WakapiService
from src.core.dependencies.auth import keycloak_admin

user_data_repository = UserDataRepository(UserData)
user_business_data_repository = UserBusinessDataRepository(UserBusinessData)
user_data_service = UserDataService(user_data_repository, user_business_data_repository, keycloak_admin)

wakapi_repository = WakapiUserRepository(Users)
wakapi_service = WakapiService(wakapi_repository)
