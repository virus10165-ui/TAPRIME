from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int | None
    department_id: int | None
    email: EmailStr
    full_name: str
    role: UserRole
    phone_number: str | None
    is_2fa_enabled: bool
    is_active: bool


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    department_id: int | None = None
