import imaplib
import email
import re
import os
from email.header import decode_header

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

if not EMAIL_USER or not EMAIL_PASS:
    print("Faltan variables EMAIL_USER o EMAIL_PASS")
    exit()

# conectar a Gmail
mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(EMAIL_USER, EMAIL_PASS)

mail.select("INBOX")

# buscar correos VUCE
status, messages = mail.search(None, '(FROM "pba@consultorabarreto.com")')

ids = messages[0].split()

# tomar solo los 5 más recientes
ids = ids[-5:]

for num in reversed(ids):

    status, data = mail.fetch(num, "(RFC822)")
    msg = email.message_from_bytes(data[0][1])

    subject, encoding = decode_header(msg["subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")

    # detectar evento
    estado = None

    if "Se ha iniciado el Trámite" in subject:
        estado = "EN_REVISION"

    elif "Se ha Admitido la Respuesta" in subject:
        estado = "RESPUESTA_ADMITIDA"

    elif "Se ha culminado el trámite" in subject:
        estado = "TRAMITE_CULMINADO"

    elif "Se Anula por Caducidad" in subject:
        estado = "CADUCADO"

    # extraer datos
    suce = re.search(r"SUCE\s+(\d+)", subject)
    expediente = re.search(r"Expediente\s+(\d+)", subject)

    suce_id = suce.group(1) if suce else None
    expediente_id = expediente.group(1) if expediente else None

    print("SUBJECT:", subject)
    print("SUCE:", suce_id)
    print("EXPEDIENTE:", expediente_id)
    print("ESTADO:", estado)
    print("-" * 40)