from fastapi import APIRouter

from .blog.api.endpoint.blog import router as blog_router
from .fellows.api.endpoint.project import router as project_router
from .map.api.endpoint.map import router as map_router
from .open_api.api.endpoint.fiscal import router as fiscal_router
from .open_api.api.endpoint.welfare import router as welfare_router
from .user.api.endpoint.cloud import router as cloud_router
from .user.api.endpoint.user_data import router as user_data_router
from .user.api.endpoint.wakapi import router as wakapi_router

router = APIRouter()

router.include_router(user_data_router, prefix="/user/data", tags=["user_data"])
router.include_router(fiscal_router, prefix="/fiscal", tags=["fiscal"])
router.include_router(welfare_router, prefix="/welfare", tags=["welfare"])
router.include_router(map_router, prefix="/map", tags=["map"])
router.include_router(wakapi_router, prefix="/wakapi", tags=["wakapi"])
router.include_router(project_router, prefix="/project", tags=["project"])
router.include_router(cloud_router, prefix="/cloud", tags=["cloud"])
router.include_router(blog_router, prefix="/blog", tags=["blog"])
