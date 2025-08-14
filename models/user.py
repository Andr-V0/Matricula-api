from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class User(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id", default=None)
    nombre: str
    apellido: str
    identidad: str
    email: EmailStr
    
    # Campos para almacenar los ObjectId de los roles
    role1: Optional[ObjectId] = None
    role2: Optional[ObjectId] = None
    role3: Optional[ObjectId] = None
    
    fechaAlta: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserCreate(BaseModel):
    nombre: str
    apellido: str
    identidad: str
    email: EmailStr
