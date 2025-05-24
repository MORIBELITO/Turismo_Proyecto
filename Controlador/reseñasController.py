from modelo.conexion import db

def obtener_reseñas():
    reseñas = []
    coleccion = db.collection('reseñas')
    docs = coleccion.stream()
    for doc in docs:
        reseñas.append(doc.to_dict())
    return reseñas

def guardar_reseña(data):
    db.collection('reseñas').add(data)
