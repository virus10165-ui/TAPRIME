import enum


class UserRole(str, enum.Enum):
    """Роли пользователей.

    SUPERADMIN — уровень платформы, company_id = NULL, управляет компаниями-тенантами.
    Остальные роли — внутри одной компании-тенанта (см. концепцию проекта):
      COMPANY_ADMIN — техническая роль, настраивает оргструктуру, шаблоны и цепочки согласования
      ORG_HEAD      — руководитель организации
      DEPT_HEAD     — руководитель подразделения
      EMPLOYEE      — сотрудник
    """

    SUPERADMIN = "superadmin"
    COMPANY_ADMIN = "company_admin"
    ORG_HEAD = "org_head"
    DEPT_HEAD = "dept_head"
    EMPLOYEE = "employee"


class MemoFieldType(str, enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"


class CurrencyCode(str, enum.Enum):
    KZT = "KZT"
    USD = "USD"
    EUR = "EUR"


class MemoStatus(str, enum.Enum):
    PENDING = "pending"       # на согласовании
    APPROVED = "approved"     # согласована всеми
    REJECTED = "rejected"     # отклонена на каком-то шаге


class ApprovalStepStatus(str, enum.Enum):
    WAITING = "waiting"       # ещё не наступила очередь (предыдущие шаги не пройдены)
    PENDING = "pending"       # сейчас на этом шаге, ждём решения согласующего
    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationType(str, enum.Enum):
    APPROVAL_NEEDED = "approval_needed"  # записка дошла до вас — нужно решение
    OVERDUE = "overdue"                  # шаг просрочен (уходит согласующему и автору)
    DECIDED = "decided"                  # по записке принято финальное решение (автору)
