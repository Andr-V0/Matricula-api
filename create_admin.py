
import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
from bson import ObjectId

# --- Configuración de la ruta del proyecto ---
# Esto permite que el script encuentre los módulos de tu aplicación (como utils, controllers)
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# --- Carga de variables de entorno ---
load_dotenv()

# --- Importaciones de la aplicación ---
# Se importan después de ajustar la ruta
from utils.firebase import create_firebase_user
from controllers.auth_controller import generate_password

def create_first_admin():
    """
    Script para crear el primer usuario administrador si no existe ninguno.
    """
    try:
        # --- Conexión a la Base de Datos ---
        client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
        db = client[os.getenv("DATABASE_NAME")]
        
        print("Conexión a la base de datos exitosa.")

        # --- Colecciones ---
        users_collection = db["users"]
        admins_collection = db["Administradores"]
        roles_collection = db["tipos_usuarios"]

        # 1. Verificar si ya existe un administrador
        admin_role = roles_collection.find_one({"codigo": "ADM"})
        if not admin_role:
            print("Error: El rol 'ADM' no existe en la colección 'tipos_usuario'.")
            print("Por favor, asegúrese de que los roles iniciales estén cargados en la base de datos.")
            return

        admin_role_id = admin_role["_id"]
        
        # Buscamos si algún usuario ya tiene el rol de admin
        existing_admin = users_collection.find_one({"$or": [{"role1": admin_role_id}, {"role2": admin_role_id}, {"role3": admin_role_id}]})
        
        if existing_admin:
            print("Ya existe un usuario administrador en el sistema.")
            # Opcionalmente, buscar su correo para mostrarlo
            admin_doc = admins_collection.find_one({"identidad": existing_admin.get("identidad")})
            if admin_doc:
                print(f"El correo del administrador existente es: {admin_doc.get('email_institucional')}")
            return

        print("No se encontraron administradores. Creando el primero...")

        # 2. Datos del primer administrador (puedes cambiar estos valores)
        admin_details = {
            "nombre": "Admin",
            "apellido": "Principal",
            "identidad": "0000000000000",
            "email": "admin@example.com" # Email personal de referencia
        }

        # 3. Generar credenciales institucionales
        nombre_normalizado = admin_details["nombre"].lower().replace(" ", "")
        apellido_normalizado = admin_details["apellido"].lower().replace(" ", "")
        email_institucional = f"{nombre_normalizado}.{apellido_normalizado}@admin.com"
        password_generada = generate_password()

        print(f"Email institucional generado: {email_institucional}")

        # 4. Crear usuario en Firebase
        try:
            print("Creando usuario en Firebase...")
            create_firebase_user(email_institucional, password_generada)
            print("Usuario creado en Firebase exitosamente.")
        except Exception as e:
            if "EMAIL_EXISTS" in str(e):
                print(f"Error: El correo institucional '{email_institucional}' ya existe en Firebase.")
                print("Puede que necesites limpiar los usuarios de Firebase o cambiar los datos en 'admin_details' en el script.")
            else:
                print(f"Error inesperado al crear usuario en Firebase: {e}")
            return

        # 5. Crear los documentos en MongoDB
        print("Insertando documentos en MongoDB...")
        
        # Documento en la colección 'users'
        user_doc = admin_details.copy()
        user_doc["role1"] = admin_role_id
        users_collection.insert_one(user_doc)
        print("Documento creado en 'users'.")

        # Documento en la colección 'Administradores'
        admin_doc_data = {
            "nombre": admin_details["nombre"],
            "apellido": admin_details["apellido"],
            "identidad": admin_details["identidad"],
            "email_institucional": email_institucional,
            "password_generada": password_generada,
        }
        admins_collection.insert_one(admin_doc_data)
        print("Documento creado en 'Administradores'.")

        print("\n--- ¡Proceso completado! ---")
        print("El primer usuario administrador ha sido creado con éxito.")
        print(f"\nCorreo de inicio de sesión: {email_institucional}")
        print(f"Contraseña: {password_generada}\n")

    except Exception as e:
        print(f"\nOcurrió un error durante la ejecución del script: {e}")
    finally:
        if 'client' in locals():
            client.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    create_first_admin()
