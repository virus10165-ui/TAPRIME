from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.api.routes import auth, departments, platform, users
from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.user import User

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth.router)
app.include_router(platform.router)
app.include_router(departments.router)
app.include_router(users.router)


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


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
