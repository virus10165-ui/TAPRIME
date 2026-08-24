import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.api.routes import auth, departments, memo_templates, memos, notifications, platform, reports, users
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.user import User
from app.services.memo_service import scan_overdue_steps

logger = logging.getLogger("taprime")

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth.router)
app.include_router(platform.router)
app.include_router(departments.router)
app.include_router(users.router)
app.include_router(memo_templates.router)
app.include_router(memos.router)
app.include_router(notifications.router)
app.include_router(reports.router)

scheduler = BackgroundScheduler()


def _run_overdue_scan() -> None:
    db: Session = SessionLocal()
    try:
        found = scan_overdue_steps(db)
        if found:
            logger.info("overdue scan: %s шагов согласования просрочено, отправлены уведомления", found)
    finally:
        db.close()


@app.on_event("startup")
def ensure_first_superadmin() -> None:
    """Гарантирует, что при первом старте существует хотя бы один суперадмин
    платформы — иначе некому создавать первую компанию через /platform/companies."""
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.FIRST_SUPERADMIN_EMAIL).first()
        if existing is None:
            superadmin = User(
                company_id=None,
                email=settings.FIRST_SUPERADMIN_EMAIL,
                hashed_password=hash_password(settings.FIRST_SUPERADMIN_PASSWORD),
                full_name="Platform Superadmin",
                role=UserRole.SUPERADMIN,
            )
            db.add(superadmin)
            db.commit()
    finally:
        db.close()


@app.on_event("startup")
def start_scheduler() -> None:
    # Каждые 15 минут проверяем, не истёк ли срок согласования у активных шагов
    scheduler.add_job(_run_overdue_scan, "interval", minutes=15, id="overdue_scan", replace_existing=True)
    scheduler.start()


@app.on_event("shutdown")
def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
