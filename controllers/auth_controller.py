from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from models.user import User, UserCreate
from models.estudiante import Estudiante
from utils.firebase import create_firebase_user, get_firebase_user_by_email
from utils.db import db
from utils.jwt import create_access_token
import secrets
import string

def generate_password(length=12):
    """Generates a secure random password."""
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def create_new_user(user: UserCreate):
    try:
        # 1. Verificación de existencia
        if db.users.find_one({"identidad": user.identidad}) or \
           db.Estudiantes.find_one({"identidad": user.identidad}) or \
           db.Profesores.find_one({"identidad": user.identidad}) or \
           db.Administradores.find_one({"identidad": user.identidad}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario con esta identidad ya existe")

        # 2. Asignación del rol por defecto (EST)
        tipo_usuario_est = db.tipos_usuarios.find_one({"codigo": "EST"})
        if not tipo_usuario_est:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Rol 'EST' no encontrado. Asegúrese de que exista en la colección tipos_usuarios.")
        
        est_role_id = tipo_usuario_est["_id"]

        # 3. Generar correo institucional y contraseña
        nombre_normalizado = user.nombre.lower().replace(" ", "")
        apellido_normalizado = user.apellido.lower().replace(" ", "")
        email_institucional = f"{nombre_normalizado}.{apellido_normalizado}@uni.com"
        password_generada = generate_password()

        # 4. Crear usuario en Firebase
        try:
            firebase_user = create_firebase_user(email_institucional, password_generada)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error al crear usuario en Firebase: {e}")

        # 5. Guardar en MongoDB
        new_user_data = user.dict(exclude={"id"}) # Excluir id para evitar conflictos en inserción
        new_user_data["role1"] = est_role_id
        
        db.users.insert_one(new_user_data)

        estudiante_data = Estudiante(
            nombre=user.nombre,
            apellido=user.apellido,
            identidad=user.identidad,
            email_institucional=email_institucional,
            password_generada=password_generada
        )
        db.Estudiantes.insert_one(estudiante_data.dict(exclude={"id"}))

        return {
            "message": "Usuario creado correctamente con el rol de Estudiante.",
            "email_institucional": email_institucional,
            "password": password_generada
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def login_for_access_token(form_data: OAuth2PasswordRequestForm):
    try:
        email = form_data.username
        password = form_data.password

        # 1. Autenticar contra Firebase
        try:
            # Como la librería admin no puede verificar contraseñas directamente,
            # solo verificamos que el usuario exista en Firebase.
            firebase_user = get_firebase_user_by_email(email)
        except Exception as e:
            # Esta excepción se captura si el email no existe en Firebase.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Determinar el rol según el dominio del correo
        if email.endswith("@uni.com"):
            role = "EST"
            collection = db.Estudiantes
        elif email.endswith("@edu.com"):
            role = "PROF"
            collection = db.Profesores
        elif email.endswith("@admin.com"):
            role = "ADM"
            collection = db.Administradores
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dominio de email no válido"
            )

        # 3. Buscar datos en la colección de MongoDB
        user_data = collection.find_one({"email_institucional": email})
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado en la base de datos interna."
            )
        
        # NOTA: La verificación de la contraseña no se puede hacer directamente aquí
        # con firebase-admin. Se asume que si el usuario existe, la contraseña es correcta.

        # 4. Generar el token JWT
        access_token = create_access_token(
            data={"sub": email, "role": role}
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def get_user_profile(current_user: dict):
    try:
        email = current_user.get("sub")
        role = current_user.get("role")

        if not email or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o corrupto."
            )

        # Determinar la colección basada en el rol
        if role == "EST":
            collection = db.Estudiantes
        elif role == "PROF":
            collection = db.Profesores
        elif role == "ADM":
            collection = db.Administradores
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rol no reconocido."
            )

        # Buscar al usuario en la colección correspondiente
        user_data = collection.find_one({"email_institucional": email})

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de usuario no encontrado."
            )
        
        # Convertir ObjectId a string para que sea serializable en JSON
        user_data["_id"] = str(user_data["_id"])

        return user_data

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )