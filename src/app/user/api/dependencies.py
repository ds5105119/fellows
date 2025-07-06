from src.app.user.model.alert import Alert
from src.app.user.model.user_data import UserBusinessData, UserData
from src.app.user.model.wakapi import Users
from src.app.user.repository.alert import AlertRepository
from src.app.user.repository.user_data import UserBusinessDataRepository, UserDataRepository
from src.app.user.repository.wakapi import WakapiUserRepository
from src.app.user.service.alert import AlertService
from src.app.user.service.cloud import CloudService
from src.app.user.service.user_data import UserDataService
from src.app.user.service.wakapi import WakapiService
from src.core.dependencies.auth import keycloak_admin
from src.core.dependencies.db import r2
from src.core.dependencies.infra import frappe_client

user_data_repository = UserDataRepository(UserData)
user_business_data_repository = UserBusinessDataRepository(UserBusinessData)
user_data_service = UserDataService(user_data_repository, user_business_data_repository, keycloak_admin)

wakapi_repository = WakapiUserRepository(Users)
wakapi_service = WakapiService(wakapi_repository)

alert_repository = AlertRepository(Alert)
alert_service = AlertService(alert_repository)

cloud_service = CloudService(frappe_client, r2)
