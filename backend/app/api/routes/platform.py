from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.session import get_db
from app.models.company import Company
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyOut

router = APIRouter(prefix="/platform", tags=["platform"])

_require_superadmin = require_roles(UserRole.SUPERADMIN)


@router.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(_require_superadmin),
) -> Company:
    """Ручной онбординг новой компании-клиента: суперадмин платформы создаёт
    компанию и первого администратора компании одним запросом."""
    existing = db.query(User).filter(User.email == payload.admin_email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже используется")

    company = Company(name=payload.name)
    db.add(company)
    db.flush()  # получить company.id до создания пользователя

    admin_user = User(
        company_id=company.id,
        email=payload.admin_email,
        hashed_password=hash_password(payload.admin_password),
        full_name=payload.admin_full_name,
        role=UserRole.COMPANY_ADMIN,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(company)
    return company


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db), _: User = Depends(_require_superadmin)) -> list[Company]:
    return db.query(Company).order_by(Company.id).all()
