# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request
from BD.conexion import db 
import firebase_admin
from firebase_admin import credentials, firestore
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import threading
import time

app = Flask(__name__)

# Variables globales
datos_entrenamiento = None
modelo_entrenado = None
precision_modelo = None

# Cargar todos los documentos desde Firestore
def cargar_datos():
    docs = db.collection('Reseñas').stream()
    lista = []
    for doc in docs:
        d = doc.to_dict()
        try:
            visitas = int(d.get('visitas'))
            accesibles = int(d.get('accesibles'))
            anio = int(d.get('anio'))
            accesibilidad = str(d.get('accesibilidad')).strip().capitalize()
            lugar = d.get('lugar') or d.get('nombreLugar') or "Desconocido"

            if accesibilidad not in ['Baja', 'Media', 'Alta']:
                continue
            if None in [visitas, accesibles, anio] or not accesibilidad:
                continue

            lista.append({
                'Visitas': visitas,
                'Servicios_Accesibles': accesibles,
                'Año': anio,
                'Accesibilidad': accesibilidad,
                'Destino': lugar
            })
        except Exception:
            continue
    df = pd.DataFrame(lista)
    print("Distribución de clases:", df['Accesibilidad'].value_counts().to_dict())
    return df

# Entrenar el modelo
def entrenar(df):
    global modelo_entrenado, precision_modelo, datos_entrenamiento

    if df.empty or len(df) < 5:
        return False, "No hay datos suficientes para entrenar."

    X = df[['Visitas', 'Servicios_Accesibles', 'Año']]
    Y = df['Accesibilidad']

    x_train, x_test, y_train, y_test = train_test_split(X, Y, train_size=0.7, random_state=42)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight='balanced',
        random_state=42
    )
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    precision = accuracy_score(y_test, y_pred)

    modelo_entrenado = model
    precision_modelo = precision
    datos_entrenamiento = df

    return True, f"Modelo entrenado con éxito (precisión: {round(precision * 100, 2)}%)"

# Graficar árbol de decisión (del primer estimador del bosque)
def graficar_arbol_decision():
    global modelo_entrenado
    plt.figure(figsize=(24, 18))
    estimator = modelo_entrenado.estimators_[0]
    plot_tree(
        estimator,
        feature_names=['Visitas', 'Servicios_Accesibles', 'Año'],
        class_names=modelo_entrenado.classes_,
        filled=True,
        rounded=True,
        fontsize=12
    )
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

# Graficar barras por destino
def graficar_barra_accesibilidad():
    global datos_entrenamiento
    df = datos_entrenamiento
    plt.figure(figsize=(12, 6))
    plt.bar(df['Destino'], df['Servicios_Accesibles'], color='#4e79a7')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Destino Turístico')
    plt.ylabel('N° de Servicios Accesibles')
    plt.title('Accesibilidad por Destino')
    plt.ylim([0, max(df['Servicios_Accesibles']) + 1])
    plt.grid(True, linestyle='--', axis='y')
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

# Ruta principal
@app.route('/')
def index():
    df = cargar_datos()
    entrenado, mensaje = entrenar(df)
    if not entrenado:
        return f"<h3>{mensaje}</h3>"

    graf_arbol = graficar_arbol_decision()
    graf_barra = graficar_barra_accesibilidad()

    html = f"""
    <html>
    <head>
        <title>Predicción de Accesibilidad Turística</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; }}
            h2 {{ color: #2c3e50; }}
            img {{ max-width: 100%; border: 1px solid #ccc; margin-top: 15px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ccc; padding: 6px; text-align: center; }}
            th {{ background-color: #ecf0f1; }}
        </style>
    </head>
    <body>
        <h2>{mensaje}</h2>
        <p><strong>Documentos revisados:</strong> {len(df)}</p>
        <h3>Árbol de Decisión (1er Árbol del Bosque)</h3>
        <img src="data:image/png;base64,{graf_arbol}" alt="Árbol de Decisión">
        <h3>Accesibilidad por Destino</h3>
        <img src="data:image/png;base64,{graf_barra}" alt="Gráfico de Barras">
        <h3>Datos de Entrenamiento</h3>
        {df.to_html(index=False)}
    </body>
    </html>
    """
    return html

# Ruta de predicción
@app.route('/predecir', methods=['POST'])
def predecir():
    global modelo_entrenado
    if modelo_entrenado is None:
        return jsonify({"error": "Modelo no entrenado aún. Abre la ruta / para entrenar."}), 400

    data = request.json
    try:
        visitas = int(data.get('visitas'))
        accesibles = int(data.get('accesibles'))
        anio = int(data.get('anio'))
    except:
        return jsonify({"error": "visitas, accesibles y anio deben ser números válidos"}), 400

    pred = modelo_entrenado.predict([[visitas, accesibles, anio]])
    return jsonify({"prediccion": pred[0]})

# Ruta para consultar la precisión actual
@app.route('/precision')
def precision():
    global precision_modelo
    if precision_modelo is None:
        return jsonify({"error": "Modelo aún no entrenado"}), 400
    return jsonify({"precision": round(precision_modelo * 100, 2)})

# Entrenamiento automático cada segundo
def reentrenar_periodicamente():
    while True:
        try:
            df = cargar_datos()
            entrenado, mensaje = entrenar(df)
            print("[AUTO] Modelo reentrenado - Documentos:", len(df))
        except Exception as e:
            print("[ERROR] en reentrenamiento:", e)
        time.sleep(10)

threading.Thread(target=reentrenar_periodicamente, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True)
