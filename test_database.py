import pytest
from utils.db import test_connection, client, db
import os

# load_dotenv() ya se llama en utils.db

def test_env_variables():
    """Prueba si las variables están configuradas."""
    mongodb_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME")
    assert mongodb_uri is not None, "MONGODB_URI no está configurado."
    assert database_name is not None, "DATABASE_NAME no está configurado."
    print(f"URI de la base de datos: {mongodb_uri}")
    print(f"Nombre de la base de datos: {database_name}")

def test_db_connection():
    """Prueba la conexión a la base de datos."""
    # La prueba pasará si test_connection() no genera una excepción.
    test_connection()

def test_mongo_client():
    """Prueba si MongoDB está inicializado."""
    assert client is not None, "El cliente de MongoDB es None."

def test_get_collection():
    """Prueba si se puede recuperar una colección."""
    db_name = os.getenv("DATABASE_NAME")
    assert db.name == db_name, f"El nombre de la base de datos no coincide. Esperado: {db_name}, Obtenido: {db.name}"
    
    # Comprueba si existe una colección (por ejemplo, 'tipos_usuarios')
    coll_users = db.tipos_usuarios
    assert coll_users is not None, "No se pudo obtener la colección 'tipos_usuarios'."
