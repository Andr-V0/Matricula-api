from fastapi import HTTPException, status
from utils.db import db
from bson import ObjectId
from models.user_role import UserRoleUpdate
from models.profesor import Profesor
from models.administrador import Administrador
from controllers.auth_controller import generate_password
from utils.firebase import create_firebase_user

def update_user_role_by_id(user_id: str, role_update: UserRoleUpdate):
    try:
        # 1. Validar ObjectId
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ID de usuario no válido.")
        
        user_oid = ObjectId(user_id)

        # 2. Buscar usuario
        user = db.users.find_one({"_id": user_oid})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

        # 3. Validar rol
        role_code = role_update.role_code.upper()
        if role_code not in ["PROF", "ADM"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El rol debe ser 'PROF' o 'ADM'.")

        new_role_doc = db.tipos_usuarios.find_one({"codigo": role_code})
        if not new_role_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El rol con código '{role_code}' no existe.")
        
        new_role_id = new_role_doc["_id"]

        # 4. Verificar roles duplicados
        if new_role_id in [user.get("role1"), user.get("role2"), user.get("role3")]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya tiene este rol.")

        # 5. Encontrar slot de rol vacío
        role_slot = None
        if not user.get("role2"):
            role_slot = "role2"
        elif not user.get("role3"):
            role_slot = "role3"
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya tiene el número máximo de roles.")

        # 6. Generar nuevas credenciales
        nombre_normalizado = user["nombre"].lower().replace(" ", "")
        apellido_normalizado = user["apellido"].lower().replace(" ", "")
        domain = "edu.com" if role_code == "PROF" else "admin.com"
        new_email = f"{nombre_normalizado}.{apellido_normalizado}@{domain}"
        new_password = generate_password()

        # 7. Crear usuario en Firebase
        try:
            create_firebase_user(new_email, new_password)
        except Exception as e:
            # Verificar si el error es porque el email ya existe
            if "EMAIL_EXISTS" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El correo institucional '{new_email}' ya está en uso en Firebase."
                )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear usuario en Firebase: {e}")

        # 8. Crear documento en la colección correspondiente
        user_details = {
            "nombre": user["nombre"],
            "apellido": user["apellido"],
            "identidad": user["identidad"],
            "email_institucional": new_email,
            "password_generada": new_password,
        }

        if role_code == "PROF":
            db.Profesores.insert_one(Profesor(**user_details).dict(by_alias=True))
        elif role_code == "ADM":
            db.Administradores.insert_one(Administrador(**user_details).dict(by_alias=True))

        # 9. Actualizar documento del usuario
        db.users.update_one(
            {"_id": user_oid},
            {"$set": {role_slot: new_role_id}}
        )

        return {
            "message": f"Rol '{role_code}' asignado correctamente al usuario.",
            "new_email": new_email,
            "new_password": new_password
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_all_users_with_roles():
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "tipos_usuarios",
                    "localField": "role1",
                    "foreignField": "_id",
                    "as": "role1_info"
                }
            },
            {
                "$lookup": {
                    "from": "tipos_usuarios",
                    "localField": "role2",
                    "foreignField": "_id",
                    "as": "role2_info"
                }
            },
            {
                "$lookup": {
                    "from": "tipos_usuarios",
                    "localField": "role3",
                    "foreignField": "_id",
                    "as": "role3_info"
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "nombre": 1,
                    "apellido": 1,
                    "roles": {
                        "$filter": {
                            "input": {
                                "$concatArrays": [
                                    "$role1_info.codigo",
                                    "$role2_info.codigo",
                                    "$role3_info.codigo"
                                ]
                            },
                            "as": "role",
                            "cond": { "$ne": [ "$$role", None ] }
                        }
                    }
                }
            }
        ]
        users = list(db.users.aggregate(pipeline))
        return users
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_all_students():
    try:
        students = list(db.Estudiantes.find({}, {"_id": 0, "nombre": 1, "apellido": 1}))
        return students
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_all_professors():
    try:
        professors = list(db.Profesores.find({}, {"_id": 0, "nombre": 1, "apellido": 1}))
        return professors
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_all_admins():
    try:
        admins = list(db.Administradores.find({}, {"_id": 0, "nombre": 1, "apellido": 1}))
        return admins
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))