from fastapi import HTTPException, status
from models.tipos_usuario import TiposUsuario
from utils.db import db
from bson import ObjectId

def create_new_tipo_usuario(tipo_usuario: TiposUsuario):
    try:
 
        if db.tipos_usuarios.find_one({"codigo": tipo_usuario.codigo}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de usuario con este codigo ya existe")

        db.tipos_usuarios.insert_one(tipo_usuario.dict())
        return {"message": "Tipo de usuario creado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_all_tipos_usuario():
    try:
        tipos_usuario = list(db.tipos_usuarios.find({}, {"_id": 1, "codigo": 1}))
        for tipo in tipos_usuario:
            tipo["_id"] = str(tipo["_id"])
        return tipos_usuario
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_tipo_usuario_by_id(id: str):
    try:
        tipo_usuario = db.tipos_usuarios.find_one({"_id": ObjectId(id)}, {"_id": 0, "nombre": 1})
        if not tipo_usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de usuario no encontrado")
        return tipo_usuario
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def delete_tipo_usuario_by_id(id: str):
    try:
        # Validar que no existan usuarios con este tipo
        if db.users.find_one({"tipoUsuario": ObjectId(id)}):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puede borrar tipo de usuario con uno asociado")

        result = db.tipos_usuarios.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de usuario no encontrado")
        return {"message": "Tipo de usuario borrado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))