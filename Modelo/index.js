import express from 'express';
import cors from 'cors';
import admin from 'firebase-admin';
import { readFile } from 'fs/promises';

// Leer y parsear credenciales Firebase
const serviceAccount = JSON.parse(await readFile(new URL('./firebase-key.json', import.meta.url)));

// Inicializar Firebase Admin
admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

const db = admin.firestore();

const app = express();

app.use(cors());
app.use(express.json());

// Ruta para obtener todos los documentos de la colección "turismos"
app.get('/resenas', async (req, res) => {
  try {
    const snapshot = await db.collection('Reseñas').get();
    if (snapshot.empty) {
      return res.status(404).json({ message: 'No hay documentos en Reseñas' });
    }
    const turismos = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    res.json(turismos);
  } catch (error) {
    console.error('Error obteniendo turismos:', error);
    res.status(500).json({ error: 'Error al obtener turismos' });
  }
});

// Puerto
const PORT = 3000;

app.listen(PORT, () => {
  console.log(`Servidor iniciado en http://localhost:${PORT}`);
});
