import requests
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")
SESSION_ID = os.getenv("VUCE_SESSION")

if not DATABASE_URL:
    raise Exception("DATABASE_URL no definida")

if not SESSION_ID:
    raise Exception("VUCE_SESSION no definida")

# conexión a postgres
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

url = "https://authorize.vuce.gob.pe/api/mr-administracion/solicitud/buscar"

params = {
    "componente": 1,
    "fechaRegistro.min": "2025-09-11",
    "fechaRegistro.max": "2026-12-31",
    "cantidad": 10,
    "pagina": 1,
    "etapa": "TODOS"
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://www.vuce.gob.pe",
    "Referer": "https://www.vuce.gob.pe/",
    "X-Sesion-Id": SESSION_ID
}

response = requests.get(url, headers=headers, params=params)

if response.status_code != 200:
    print("Error API:", response.status_code)
    exit()

data = response.json()

if "_embedded" not in data:
    print("Respuesta inesperada de VUCE (posible sesión expirada)")
    exit()

solicitudes = data["_embedded"]["solicitudes"]

cambios = 0

for s in solicitudes:

    solicitud_id = s["id"]
    codigo = s["codigo"]
    tipo = s["tipo"]

    entidad = s["orden"]["entidad"]["nombre"]

    estado_codigo = s["orden"]["estado"]["codigo"]
    estado_desc = s["orden"]["estado"]["descripcion"]

    fecha_registro = s["fechaRegistro"]

    # verificar si existe
    cursor.execute(
        "SELECT estado_codigo FROM solicitudes WHERE id = %s",
        (solicitud_id,)
    )

    result = cursor.fetchone()

    if result is None:

        cursor.execute("""
        INSERT INTO solicitudes (
            id,
            codigo,
            tipo,
            entidad,
            estado_codigo,
            estado_descripcion,
            fecha_registro
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            solicitud_id,
            codigo,
            tipo,
            entidad,
            estado_codigo,
            estado_desc,
            fecha_registro
        ))

        cambios += 1
        print("Nueva solicitud:", codigo)

    else:

        estado_db = result[0]

        if estado_db != estado_codigo:

            cursor.execute("""
            UPDATE solicitudes
            SET estado_codigo = %s,
                estado_descripcion = %s,
                fecha_actualizacion = NOW()
            WHERE id = %s
            """, (
                estado_codigo,
                estado_desc,
                solicitud_id
            ))

            cambios += 1
            print("Cambio de estado:", codigo)

conn.commit()

if cambios == 0:
    print("No hay cambios")
else:
    print(f"{cambios} cambios detectados")

conn.close()
