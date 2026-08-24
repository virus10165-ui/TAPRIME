from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_tenant_user, require_roles
from app.db.session import get_db
from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentOut

router = APIRouter(prefix="/departments", tags=["departments"])

_require_company_admin = require_roles(UserRole.COMPANY_ADMIN)


@router.get("", response_model=list[DepartmentOut])
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_user),
) -> list[Department]:
    # Тенант-изоляция: всегда фильтруем по company_id из токена, никогда — из query-параметров
    return db.query(Department).filter(Department.company_id == current_user.company_id).order_by(Department.id).all()


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_company_admin),
) -> Department:
    if payload.parent_id is not None:
        parent = db.get(Department, payload.parent_id)
        if parent is None or parent.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Родительский отдел не найден")

    department = Department(
        company_id=current_user.company_id,
        name=payload.name,
        parent_id=payload.parent_id,
        head_user_id=payload.head_user_id,
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department
