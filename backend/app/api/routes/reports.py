from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.enums import ApprovalStepStatus, UserRole
from app.models.memo import Memo, MemoApprovalStep
from app.models.user import User
from app.schemas.report import OverdueStepOut

router = APIRouter(prefix="/reports", tags=["reports"])

_require_oversight = require_roles(UserRole.COMPANY_ADMIN, UserRole.ORG_HEAD)


@router.get("/overdue", response_model=list[OverdueStepOut])
def overdue_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_oversight),
) -> list[OverdueStepOut]:
    """Кто прямо сейчас тормозит согласование: активные шаги, у которых срок
    уже прошёл. deadline_at не сдвигается при просрочке, поэтому «минус» —
    это просто (сейчас - deadline_at), посчитанный на лету."""
    now = datetime.now(timezone.utc)
    steps = (
        db.query(MemoApprovalStep)
        .join(Memo, Memo.id == MemoApprovalStep.memo_id)
        .options(joinedload(MemoApprovalStep.memo))
        .filter(
            Memo.company_id == current_user.company_id,
            MemoApprovalStep.status == ApprovalStepStatus.PENDING,
            MemoApprovalStep.deadline_at < now,
        )
        .order_by(MemoApprovalStep.deadline_at)
        .all()
    )

    return [
        OverdueStepOut(
            memo_id=step.memo_id,
            step_order=step.step_order,
            approver_id=step.approver_id,
            deadline_at=step.deadline_at,
            overdue_hours=round((now - step.deadline_at).total_seconds() / 3600, 1),
        )
        for step in steps
    ]
