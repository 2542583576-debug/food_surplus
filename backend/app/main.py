import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.carbon_records import router as carbon_router
from app.api.notifications import router as notifications_router
from app.api.orders import router as orders_router
from app.api.router import api_router
from app.api.stores import router as stores_router
from app.api.surplus_bags import router as surplus_bags_router
from app.api.upload import mount_uploads, router as upload_router
from app.api.users import router as users_router
from app.common.exception import (
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.services.order_service import release_expired_orders

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("food_surplus")


async def expired_order_task() -> None:
    """后台任务：每 60 秒释放超时未自提的订单库存。"""
    while True:
        try:
            await asyncio.sleep(60)
            db = SessionLocal()
            try:
                count = await asyncio.to_thread(release_expired_orders, db)
                if count:
                    logger.info("已释放 %s 个超时订单", count)
            finally:
                db.close()
        except asyncio.CancelledError:
            return
        except Exception as exc:  # pragma: no cover
            logger.exception("超时订单任务异常: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(expired_order_task())
    logger.info("%s 启动完成，数据库: %s", settings.APP_NAME, settings.MYSQL_DB)
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        engine.dispose()
        logger.info("服务已停止")


app = FastAPI(
    title=settings.APP_NAME,
    summary="惜食余量魔法袋回收项目后端接口文档",
    description="包含用户注册登录、余量魔法袋、下单核销、订单管理与碳减排统计",
    version="1.1.0",
    lifespan=lifespan,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "docExpansion": "list",
        "displayRequestDuration": True,
        "filter": True,
    },
)

# 显式来源 + credentials（不能使用 "*"）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    started = perf_counter()
    try:
        response = await call_next(request)
    finally:
        cost = (perf_counter() - started) * 1000
        logger.info(
            "%s %s -> %s (%.1fms) rid=%s",
            request.method,
            request.url.path,
            response.status_code if "response" in locals() else 500,
            cost,
            request_id,
        )
    response.headers["X-Request-ID"] = request_id
    return response


app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# v1 业务接口（认证/分类/商品/盲盒/订单）
app.include_router(api_router, prefix="/api")
# 兼容旧路径的魔法袋接口
app.include_router(users_router)
app.include_router(orders_router)
app.include_router(surplus_bags_router)
app.include_router(carbon_router)
app.include_router(stores_router)
app.include_router(notifications_router)
app.include_router(upload_router)

# 上传图片静态目录（须在路由注册后挂载，避免 /api 前缀冲突）
mount_uploads(app)


@app.get("/health", tags=["运维"], summary="健康检查")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/ready", tags=["运维"], summary="就绪检查（含数据库连通性）")
async def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        logger.error("数据库就绪检查失败: %s", exc)
        return JSONResponse(status_code=503, content={"status": "unready", "database": "error"})


@app.get("/test", tags=["运维"], summary="服务连通性测试")
async def test():
    return {"msg": "余量魔法袋后台服务正常"}
