from fastapi import APIRouter

from .blog.api.endpoint.blog import router as blog_router
from .fellows.api.endpoint.help import router as help_router
from .fellows.api.endpoint.project import router as project_router
from .fellows.api.endpoint.terms import router as terms_router
from .map.api.endpoint.map import router as map_router
from .payment.api.endpoint.payment import router as payment_router
from .user.api.endpoint.alert import router as alert_router
from .user.api.endpoint.cloud import router as cloud_router
from .user.api.endpoint.user_data import router as user_data_router
from .user.api.endpoint.wakapi import router as wakapi_router

router = APIRouter()

router.include_router(user_data_router, prefix="/user/data", tags=["user_data"])
router.include_router(alert_router, prefix="/user/alert", tags=["alert"])
router.include_router(terms_router, prefix="/term", tags=["term"])
router.include_router(map_router, prefix="/map", tags=["map"])
router.include_router(wakapi_router, prefix="/wakapi", tags=["wakapi"])
router.include_router(project_router, prefix="/project", tags=["project"])
router.include_router(cloud_router, prefix="/cloud", tags=["cloud"])
router.include_router(blog_router, prefix="/blog", tags=["blog"])
router.include_router(payment_router, prefix="/payment", tags=["payment"])
router.include_router(help_router, prefix="/help", tags=["help"])
