from pydantic import BaseModel, ConfigDict


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    parent_id: int | None
    head_user_id: int | None


class DepartmentCreate(BaseModel):
    name: str
    parent_id: int | None = None
    head_user_id: int | None = None
