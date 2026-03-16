import imaplib
import email
import re
import os
from email.header import decode_header
import gspread
from google.oauth2.service_account import Credentials

print("Script iniciado")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# -------------------------
# GOOGLE SHEETS
# -------------------------

print("Conectando a Google Sheets")

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

if not os.path.exists("credentials.json"):
    raise Exception("No existe credentials.json")

creds = Credentials.from_service_account_file(
    "credentials.json",
    scopes=scope
)

client = gspread.authorize(creds)

sheet = client.open_by_key(
    "14BuCVESXSJjrF2v9PDSa4mpkZj_L1ptfNAmayxfzcf0"
).worksheet("Hoja1")

print("Conectado a Sheets")


def actualizar_estado(expediente, estado):

    rows = sheet.get_all_records(expected_headers=[
        "EXP","PRODUCTO","TRAMITE","FABRICANTE",
        "F. INGRESO","F. NOTIF","F. RESPTA","ESTADO","F. REVISION"
    ])

    for i, row in enumerate(rows):

        if str(row["EXP"]).strip() == str(expediente).strip():

            sheet.update_cell(i + 2, 8, estado)

            print("Actualizado:", expediente, estado)
            return

    print("Expediente no encontrado:", expediente)


# -------------------------
# GMAIL
# -------------------------

print("Conectando a correo")

mail = imaplib.IMAP4_SSL("outlook.office365.com")
mail.login(EMAIL_USER, EMAIL_PASS)
mail.select("INBOX")

print("Buscando correos")

status, messages = mail.search(
    None,
    '(FROM "javiercastrob58@gmail.com" SUBJECT "VUCE")'
)

if status != "OK":
    raise Exception("Error buscando correos")

ids = messages[0].split()

print("Correos encontrados:", len(ids))

# últimos 10 correos
ids = ids[-10:]


for num in reversed(ids):

    status, data = mail.fetch(num, "(RFC822)")

    if status != "OK":
        print("Error leyendo correo")
        continue

    msg = email.message_from_bytes(data[0][1])

    subject, encoding = decode_header(msg["subject"])[0]

    if isinstance(subject, bytes):
        subject = subject.decode(
            encoding if encoding else "utf-8",
            errors="ignore"
        )

    body = ""

    if msg.is_multipart():

        for part in msg.walk():

            content_type = part.get_content_type()

            if content_type in ["text/plain", "text/html"]:

                payload = part.get_payload(decode=True)

                if payload:
                    body += payload.decode(errors="ignore")

    else:

        payload = msg.get_payload(decode=True)

        if payload:
            body = payload.decode(errors="ignore")


    texto = subject + " " + body


    # -------------------------
    # DETECTAR ESTADO
    # -------------------------
    estado = None

    if "Se ha iniciado el Trámite" in texto:
        estado = "PENDIENTE DE RESPUESTA DE LA ENTIDAD"

    elif "Se ha Admitido la Respuesta" in texto:
        estado = "RESPUESTA DEL USUARIO"

    elif "ha enviado una notificacion" in texto.lower():
        estado = "RESPUESTA DEL USUARIO"

    elif "Notificación" in texto:
        estado = "RESPUESTA DEL USUARIO"

    elif "Se ha culminado el trámite" in texto:
        estado = "APROBADO"

    elif "Documento Resolutivo" in texto:
        estado = "APROBADO"

    elif "Se Anula por Caducidad" in texto:
        estado = "CADUCADO"

    # -------------------------
    # EXTRAER EXPEDIENTE
    # -------------------------

    expediente = re.search(
        r"Expediente(?:\s+Entidad)?\s*[:\-]?\s*(\d+)",
        texto,
        re.IGNORECASE
    )

    expediente_id = expediente.group(1) if expediente else None


    print("Correo:", subject)
    print("Expediente:", expediente_id)
    print("Estado:", estado)


    if expediente_id and estado:
        actualizar_estado(expediente_id, estado)

    print("-" * 40)


print("Script terminado")