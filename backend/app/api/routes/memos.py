from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_tenant_user
from app.db.session import get_db
from app.models.enums import ApprovalStepStatus, UserRole
from app.models.memo import Memo, MemoApprovalStep
from app.models.memo_template import MemoTemplate
from app.models.user import User
from app.schemas.memo import MemoCreate, MemoDecisionRequest, MemoOut
from app.services import memo_service

router = APIRouter(prefix="/memos", tags=["memos"])


def _with_steps(query):
    return query.options(selectinload(Memo.steps))


def _get_memo_or_404(db: Session, memo_id: int, company_id: int) -> Memo:
    memo = _with_steps(db.query(Memo).filter(Memo.id == memo_id, Memo.company_id == company_id)).first()
    if memo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Записка не найдена")
    return memo


def _assert_can_view(memo: Memo, user: User) -> None:
    """Последовательное согласование распространяется и на просмотр: пока не
    наступила очередь согласующего, саму записку он тоже не видит. Автор и
    руководители компании (admin/org_head) видят записку всегда — им нужен
    полный обзор для контроля и отчётности."""
    if user.id == memo.author_id:
        return
    if user.role in (UserRole.COMPANY_ADMIN, UserRole.ORG_HEAD):
        return
    active_step = next((s for s in memo.steps if s.status == ApprovalStepStatus.PENDING), None)
    if active_step is not None and active_step.approver_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Записка вам пока не видна")


@router.post("", response_model=MemoOut, status_code=status.HTTP_201_CREATED)
def create_memo(
    payload: MemoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_user),
) -> Memo:
    template = (
        db.query(MemoTemplate)
        .options(selectinload(MemoTemplate.fields), selectinload(MemoTemplate.approval_steps))
        .filter(MemoTemplate.id == payload.template_id, MemoTemplate.company_id == current_user.company_id)
        .first()
    )
    if template is None or not template.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Вид служебной записки не найден")

    return memo_service.create_memo(db, template=template, author=current_user, raw_values=payload.values)


@router.get("/mine", response_model=list[MemoOut])
def list_my_memos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_user),
) -> list[Memo]:
    query = db.query(Memo).filter(Memo.company_id == current_user.company_id, Memo.author_id == current_user.id)
    return _with_steps(query).order_by(Memo.id.desc()).all()


@router.get("/pending-approval", response_model=list[MemoOut])
def list_pending_approval(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_user),
) -> list[Memo]:
    """Записки, которые сейчас ждут решения текущего пользователя — то есть
    только те, где его шаг уже активен (status=PENDING). Более поздние шаги
    других согласующих сюда не попадают, пока их очередь не наступит —
    это и есть последовательная видимость."""
    memo_ids = (
        db.query(MemoApprovalStep.memo_id)
        .filter(MemoApprovalStep.approver_id == current_user.id, MemoApprovalStep.status == ApprovalStepStatus.PENDING)
        .subquery()
    )
    query = db.query(Memo).filter(Memo.company_id == current_user.company_id, Memo.id.in_(memo_ids))
    return _with_steps(query).order_by(Memo.id.desc()).all()


@router.get("/{memo_id}", response_model=MemoOut)
def get_memo(
    memo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_user),
) -> Memo:
    memo = _get_memo_or_404(db, memo_id, current_user.company_id)
    _assert_can_view(memo, current_user)
    return memo


@router.post("/{memo_id}/decide", response_model=MemoOut)
def decide_memo(
    memo_id: int,
    payload: MemoDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_tenant_user),
) -> Memo:
    memo = _get_memo_or_404(db, memo_id, current_user.company_id)
    active_step = next((s for s in memo.steps if s.status == ApprovalStepStatus.PENDING), None)
    if active_step is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="У записки сейчас нет активного шага согласования")

    return memo_service.decide_step(
        db, memo=memo, step=active_step, approver=current_user, approve=payload.approve, comment=payload.comment
    )
