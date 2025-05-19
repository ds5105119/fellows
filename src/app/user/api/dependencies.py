from src.app.user.model.cloud import FileRecord
from src.app.user.model.group import Group, GroupInvitation, GroupMembership, GroupMembershipPositionLink, GroupPosition
from src.app.user.model.user_data import UserBusinessData, UserData
from src.app.user.model.wakapi import Users
from src.app.user.repository.cloud import FileRecordRepository
from src.app.user.repository.group import (
    GroupInvitationRepository,
    GroupMembershipPositionLinkRepository,
    GroupMembershipRepository,
    GroupPositionRepository,
    GroupRepository,
)
from src.app.user.repository.user_data import UserBusinessDataRepository, UserDataRepository
from src.app.user.repository.wakapi import WakapiUserRepository
from src.app.user.service.cloud import CloudService
from src.app.user.service.group import GroupService
from src.app.user.service.user_data import UserDataService
from src.app.user.service.wakapi import WakapiService
from src.core.dependencies.auth import keycloak_admin
from src.core.dependencies.db import r2

group_repository = GroupRepository(Group)
group_membership_repository = GroupMembershipRepository(GroupMembership)
group_position_repository = GroupPositionRepository(GroupPosition)
group_invitation_repository = GroupInvitationRepository(GroupInvitation)
group_membership_position_link_repository = GroupMembershipPositionLinkRepository(GroupMembershipPositionLink)
group_service = GroupService(
    group_repository,
    group_membership_repository,
    group_position_repository,
    group_invitation_repository,
    group_membership_position_link_repository,
    keycloak_admin,
)

user_data_repository = UserDataRepository(UserData)
user_business_data_repository = UserBusinessDataRepository(UserBusinessData)
user_data_service = UserDataService(user_data_repository, user_business_data_repository, keycloak_admin)

wakapi_repository = WakapiUserRepository(Users)
wakapi_service = WakapiService(wakapi_repository)

file_record_repository = FileRecordRepository(FileRecord)
cloud_service = CloudService(file_record_repository, r2)
