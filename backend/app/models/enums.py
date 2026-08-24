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
