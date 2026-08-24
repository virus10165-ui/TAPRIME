from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_tenant_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.memo_template import MemoApprovalStepTemplate, MemoTemplate, MemoTemplateField
from app.models.user import User
from app.schemas.memo_template import MemoTemplateCreate, MemoTemplateOut

router = APIRouter(prefix="/memo-templates", tags=["memo-templates"])

_require_company_admin = require_roles(UserRole.COMPANY_ADMIN)


def _with_relations(query):
    return query.options(selectinload(MemoTemplate.fields), selectinload(MemoTemplate.approval_steps))


@router.get("", response_model=list[MemoTemplateOut])
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_user),
) -> list[MemoTemplate]:
    query = db.query(MemoTemplate).filter(MemoTemplate.company_id == current_user.company_id)
    return _with_relations(query).order_by(MemoTemplate.id).all()


@router.post("", response_model=MemoTemplateOut, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: MemoTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_company_admin),
) -> MemoTemplate:
    if not payload.fields:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="У шаблона должно быть хотя бы одно поле")
    if not payload.approval_steps:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="У шаблона должна быть хотя бы один согласующий")

    # Согласующие обязаны быть сотрудниками этой же компании — иначе можно
    # было бы назначить согласующим пользователя чужого тенанта.
    approver_ids = {s.approver_id for s in payload.approval_steps}
    company_user_ids = {
        u.id
        for u in db.query(User.id).filter(User.company_id == current_user.company_id, User.id.in_(approver_ids)).all()
    }
    missing = approver_ids - company_user_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Согласующие не найдены в этой компании: {sorted(missing)}",
        )

    template = MemoTemplate(company_id=current_user.company_id, name=payload.name)
    db.add(template)
    db.flush()

    for field in payload.fields:
        db.add(
            MemoTemplateField(
                template_id=template.id,
                label=field.label,
                field_type=field.field_type,
                max_length=field.max_length,
                order_index=field.order_index,
                required=field.required,
            )
        )

    for step in payload.approval_steps:
        db.add(
            MemoApprovalStepTemplate(
                template_id=template.id,
                step_order=step.step_order,
                approver_id=step.approver_id,
                deadline_hours=step.deadline_hours,
            )
        )

    db.commit()

    return _with_relations(db.query(MemoTemplate).filter(MemoTemplate.id == template.id)).one()


@router.get("/{template_id}", response_model=MemoTemplateOut)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_user),
) -> MemoTemplate:
    query = db.query(MemoTemplate).filter(
        MemoTemplate.id == template_id, MemoTemplate.company_id == current_user.company_id
    )
    template = _with_relations(query).first()
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон не найден")
    return template
