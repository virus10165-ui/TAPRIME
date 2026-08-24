from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import ApprovalStepStatus, MemoFieldType, MemoStatus, NotificationType
from app.models.memo import Memo, MemoApprovalStep
from app.models.memo_template import MemoTemplate
from app.models.notification import Notification
from app.models.user import User


def _validate_and_build_values(template: MemoTemplate, raw_values: dict) -> dict:
    """Проверяет значения полей записки против конструктора шаблона: тип,
    обязательность, максимальная длина текста. Значения, которых нет в шаблоне,
    отбрасываются — доверяем только описанию полей, а не тому, что прислал клиент."""
    result: dict = {}
    for field in template.fields:
        key = str(field.id)
        value = raw_values.get(key)

        if value is None or value == "":
            if field.required:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Поле «{field.label}» обязательно для заполнения",
                )
            continue

        if field.field_type == MemoFieldType.TEXT:
            if not isinstance(value, str):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Поле «{field.label}» должно быть текстом")
            if field.max_length is not None and len(value) > field.max_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Поле «{field.label}»: превышена максимальная длина {field.max_length} символов",
                )
            result[key] = value

        elif field.field_type == MemoFieldType.NUMBER:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Поле «{field.label}» должно быть числом")
            result[key] = value

        elif field.field_type == MemoFieldType.CURRENCY:
            if not isinstance(value, dict) or "amount" not in value or "currency" not in value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Поле «{field.label}» должно быть вида {{amount, currency}}",
                )
            amount = value["amount"]
            currency = value["currency"]
            if not isinstance(amount, (int, float)) or isinstance(amount, bool):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Поле «{field.label}»: некорректная сумма")
            if currency not in ("KZT", "USD", "EUR"):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Поле «{field.label}»: неизвестная валюта")
            result[key] = {"amount": amount, "currency": currency}

    return result


def _activate_step(db: Session, memo: Memo, step: MemoApprovalStep) -> None:
    now = datetime.now(timezone.utc)
    step.status = ApprovalStepStatus.PENDING
    step.became_active_at = now
    step.deadline_at = now + timedelta(hours=step.deadline_hours)
    memo.current_step_order = step.step_order

    db.add(
        Notification(
            user_id=step.approver_id,
            memo_id=memo.id,
            type=NotificationType.APPROVAL_NEEDED,
            message=f"Служебная записка №{memo.id} ожидает вашего согласования",
        )
    )


def create_memo(db: Session, template: MemoTemplate, author: User, raw_values: dict) -> Memo:
    if not template.approval_steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У этого вида служебной записки не настроена цепочка согласования",
        )

    values = _validate_and_build_values(template, raw_values)

    memo = Memo(
        company_id=template.company_id,
        template_id=template.id,
        author_id=author.id,
        status=MemoStatus.PENDING,
        values=values,
    )
    db.add(memo)
    db.flush()  # получить memo.id

    steps = []
    for step_template in template.approval_steps:
        steps.append(
            MemoApprovalStep(
                memo_id=memo.id,
                step_order=step_template.step_order,
                approver_id=step_template.approver_id,
                deadline_hours=step_template.deadline_hours,
                status=ApprovalStepStatus.WAITING,
            )
        )
    db.add_all(steps)
    db.flush()

    first_step = min(steps, key=lambda s: s.step_order)
    _activate_step(db, memo, first_step)

    db.commit()
    db.refresh(memo)
    return memo


def decide_step(db: Session, memo: Memo, step: MemoApprovalStep, approver: User, approve: bool, comment: str | None) -> Memo:
    if memo.status != MemoStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Записка уже согласована/отклонена")
    if step.approver_id != approver.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы не согласующий на этом шаге")
    if memo.current_step_order != step.step_order or step.status != ApprovalStepStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сейчас не очередь этого шага")

    now = datetime.now(timezone.utc)
    step.decided_at = now
    step.comment = comment

    if not approve:
        step.status = ApprovalStepStatus.REJECTED
        memo.status = MemoStatus.REJECTED
        memo.current_step_order = None
        memo.decided_at = now
        db.add(
            Notification(
                user_id=memo.author_id,
                memo_id=memo.id,
                type=NotificationType.DECIDED,
                message=f"Служебная записка №{memo.id} отклонена",
            )
        )
        db.commit()
        db.refresh(memo)
        return memo

    step.status = ApprovalStepStatus.APPROVED

    remaining_steps = sorted(
        [s for s in memo.steps if s.step_order > step.step_order],
        key=lambda s: s.step_order,
    )
    if remaining_steps:
        _activate_step(db, memo, remaining_steps[0])
    else:
        memo.status = MemoStatus.APPROVED
        memo.current_step_order = None
        memo.decided_at = now
        db.add(
            Notification(
                user_id=memo.author_id,
                memo_id=memo.id,
                type=NotificationType.DECIDED,
                message=f"Служебная записка №{memo.id} полностью согласована",
            )
        )

    db.commit()
    db.refresh(memo)
    return memo


def scan_overdue_steps(db: Session) -> int:
    """Находит просроченные активные шаги и один раз уведомляет согласующего
    и автора записки. deadline_at не сдвигается — насколько шаг просрочен,
    видно как (сейчас - deadline_at) в отчётах. Возвращает число найденных
    просрочек (для логирования планировщика)."""
    now = datetime.now(timezone.utc)
    overdue_steps = (
        db.query(MemoApprovalStep)
        .filter(
            MemoApprovalStep.status == ApprovalStepStatus.PENDING,
            MemoApprovalStep.deadline_at < now,
            MemoApprovalStep.overdue_notified_at.is_(None),
        )
        .all()
    )

    for step in overdue_steps:
        step.is_overdue = True
        step.overdue_notified_at = now
        memo = step.memo
        db.add(
            Notification(
                user_id=step.approver_id,
                memo_id=memo.id,
                type=NotificationType.OVERDUE,
                message=f"Срок согласования служебной записки №{memo.id} истёк",
            )
        )
        db.add(
            Notification(
                user_id=memo.author_id,
                memo_id=memo.id,
                type=NotificationType.OVERDUE,
                message=f"Срок согласования вашей записки №{memo.id} истёк (сейчас на согласующем {step.approver_id})",
            )
        )

    if overdue_steps:
        db.commit()
    return len(overdue_steps)
