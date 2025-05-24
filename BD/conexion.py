import firebase_admin
from firebase_admin import credentials, firestore

# Inicialización de Firebase
cred = credentials.Certificate('modelo/firebase-key.json')  # ruta relativa
firebase_admin.initialize_app(cred)

# Instancia de la base de datos
db = firestore.client()
