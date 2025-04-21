from fastapi import APIRouter

from .map.api.endpoint.map import router as map_router
from .open_api.api.endpoint.fiscal import router as fiscal_router
from .open_api.api.endpoint.welfare import router as welfare_router
from .user.api.endpoint.user_data import router as user_data_router

router = APIRouter()

router.include_router(user_data_router, prefix="/user/data", tags=["user_data"])
router.include_router(fiscal_router, prefix="/fiscal", tags=["fiscal"])
router.include_router(welfare_router, prefix="/welfare", tags=["welfare"])
router.include_router(map_router, prefix="/map", tags=["map"])
