from pydantic import BaseModel, ConfigDict, EmailStr


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool


class CompanyCreate(BaseModel):
    """Создание новой компании-тенанта суперадмином платформы вместе с первым
    администратором компании (ручной онбординг — см. концепцию)."""

    name: str
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str
