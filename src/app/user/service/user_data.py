from fastapi import HTTPException, status
from keycloak import KeycloakAdmin
from sqlalchemy.exc import IntegrityError

from src.app.user.repository.user_data import UserBusinessDataRepository, UserDataRepository
from src.app.user.schema.user_data import *
from src.core.dependencies.auth import get_current_user, keycloak_admin
from src.core.dependencies.db import postgres_session


class UserDataService:
    def __init__(
        self,
        repository: UserDataRepository,
        user_business_data_repository: UserBusinessDataRepository,
        keycloak_admin: KeycloakAdmin,
    ):
        self.repository = repository
        self.user_business_data_repository = user_business_data_repository
        self.keycloak_admin = keycloak_admin

        """
        유저의 데이터를 관리하는 서비스
        
        Args:
            base_url (str):
            swagger_url (str):
            api_key (str):
            paths (dict):
            batch_size (int):
            timeout (int):
            api_config (ApiConfig):
        """

    async def create_user_data(
        self,
        data: UserDataDto,
        session: postgres_session,
        user: get_current_user,
    ):
        try:
            await self.repository.create(
                session,
                sub=user.sub,
                **data.model_dump(exclude_unset=True),
            )
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    async def read_user_data(
        self,
        session: postgres_session,
        user: get_current_user,
    ):
        result = await self.repository.get(
            session,
            [self.repository.model.sub == user.sub],
        )

        return result.mappings().first()

    async def update_user_data(
        self,
        data: PartialUserDataDto,
        session: postgres_session,
        user: get_current_user,
    ):
        await self.repository.update(
            session,
            [self.repository.model.sub == user.sub],
            **data.model_dump(exclude_unset=True),
        )

    async def create_business_data(
        self,
        data: UserBusinessDataDto,
        session: postgres_session,
        user: get_current_user,
    ):
        try:
            await self.user_business_data_repository.create(
                session,
                sub=user.sub,
                **data.model_dump(),
            )
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT)

    async def read_business_data(
        self,
        session: postgres_session,
        user: get_current_user,
    ):
        result = await self.user_business_data_repository.get(
            session,
            [self.user_business_data_repository.model.sub == user.sub],
        )

        return result.mappings().first()

    async def update_business_data(
        self,
        data: UserBusinessDataDto,
        session: postgres_session,
        user: get_current_user,
    ):
        await self.user_business_data_repository.update(
            session,
            [self.user_business_data_repository.model.sub == user.sub],
            **data.model_dump(),
        )

    async def read_user(self, user: get_current_user):
        from pprint import pprint

        data = await keycloak_admin.a_get_user(user.sub)
        pprint(data)
        return UserAttributes.model_validate(data["attributes"])

    async def update_user(
        self,
        data: UpdateUserAttributes,
        user: get_current_user,
    ):
        payload = await keycloak_admin.a_get_user(user.sub)
        payload["attributes"].update(data.model_dump(exclude_unset=True))
        await self.keycloak_admin.a_update_user(user_id=user.sub, payload=payload)
        return await keycloak_admin.a_get_user(user.sub)

    async def update_address_kakao(
        self,
        data: KakaoAddressDto,
        user: get_current_user,
    ):
        if data.meta.total_count == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        oidc_address = OIDCAddressDto(
            location=data.location,
            postal_code=data.documents[0].road_address.zone_no,
            region=data.documents[0].road_address.region_1depth_name,
            locality=data.documents[0].road_address.region_2depth_name,
            sub_locality=data.documents[0].address.region_3depth_name,
            country="kr",
            street=data.documents[0].road_address.address_name,
            formatted=data.documents[0].address.address_name,
        )

        payload = await keycloak_admin.a_get_user(user.sub)
        payload["attributes"].update(oidc_address.model_dump())

        await self.keycloak_admin.a_update_user(user_id=user.sub, payload=payload)
