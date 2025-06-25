// server.js
// Este archivo inicia un servidor web simple usando Express.js
// para servir tu archivo index.html.

const express = require('express');
const path = require('path'); // Módulo para trabajar con rutas de archivos
const app = express();
const PORT = process.env.PORT || 3000; // Define el puerto, usa el proporcionado por Railway o 3000 por defecto

// Configura Express para servir archivos estáticos desde el directorio actual.
// Esto significa que archivos como index.html, CSS, imágenes, etc., serán accesibles.
app.use(express.static(__dirname));

// Define una ruta para la solicitud GET a la raíz ('/').
// Cuando alguien acceda a tu URL de Railway, este handler enviará el archivo index.html.
app.get('/', (req, res) => {
    // __dirname es la ruta absoluta al directorio donde se encuentra este script (server.js).
    // path.join() construye una ruta segura para el archivo index.html.
    res.sendFile(path.join(__dirname, 'turismo.py'));
});

// Inicia el servidor y lo pone a escuchar en el puerto definido.
app.listen(PORT, () => {
    console.log(`Servidor ejecutándose en el puerto ${PORT}`);
    console.log(`Accede a http://localhost:${PORT} en tu entorno local.`);
});
