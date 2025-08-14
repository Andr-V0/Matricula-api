from fastapi import APIRouter, Depends, status
from controllers.user_controller import (
    update_user_role_by_id,
    get_all_users_with_roles,
    get_all_students,
    get_all_professors,
    get_all_admins,
)
from models.user_role import UserRoleUpdate
from utils.security import role_required
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Response Models
class UserWithRoles(BaseModel):
    nombre: str
    apellido: str
    roles: List[str]

class UserBasic(BaseModel):
    nombre: str
    apellido: str

@router.put("/users/{user_id}/role",
             dependencies=[Depends(role_required(["ADM"]))],
             summary="Update user role (Solo para Admins)",
             status_code=status.HTTP_200_OK)
def update_user_role(user_id: str, role_update: UserRoleUpdate):
    return update_user_role_by_id(user_id, role_update)

@router.get("/users/all",
            response_model=List[UserWithRoles],
            dependencies=[Depends(role_required(["ADM", "PROF"]))],
            summary="Get all users with their roles")
def get_all_users():
    return get_all_users_with_roles()

@router.get("/students/all",
            response_model=List[UserBasic],
            dependencies=[Depends(role_required(["ADM", "PROF"]))],
            summary="Get all students")
def get_all_students_route():
    return get_all_students()

@router.get("/professors/all",
            response_model=List[UserBasic],
            dependencies=[Depends(role_required(["ADM", "PROF"]))],
            summary="Get all professors")
def get_all_professors_route():
    return get_all_professors()

@router.get("/admins/all",
            response_model=List[UserBasic],
            dependencies=[Depends(role_required(["ADM", "PROF"]))],
            summary="Get all administrators")
def get_all_admins_route():
    return get_all_admins()