from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from bson import ObjectId

class Profesor(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id", default=None)
    nombre: str
    apellido: str
    identidad: str
    email_institucional: EmailStr
    password_generada: str # En un caso real, esto debería ser un hash
    rol: str = "PROF"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
