# src/pipeline_pricing.py
import os
from pathlib import Path
from email.message import EmailMessage
import smtplib

from etl_unidades import run_etl_unidades
from pricing_model import run_pricing_model

ROOT = Path(__file__).resolve().parents[1]

def send_email_with_report(report_path: Path):
    user = os.environ["GMAIL_USER"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_addr = os.environ["GMAIL_TO"]

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to_addr
    msg["Subject"] = "Reporte de precios fuera de curva – unidades"

    msg.set_content(
        "Hola,\n\n"
        "Adjunto el último reporte de precios por piso/tipología con "
        "recomendaciones de ajuste (subir, bajar o mantener).\n\n"
        "Enviado automáticamente por GitHub Actions.\n"
    )

    with report_path.open("rb") as f:
        data = f.read()

    msg.add_attachment(
        data,
        maintype="application",
        subtype=(
            "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename=report_path.name,
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, app_password)
        smtp.send_message(msg)

    print(f"Correo enviado a {to_addr} con {report_path.name}")

def main():
    clean_path = run_etl_unidades()
    report_path = run_pricing_model(clean_path)
    send_email_with_report(report_path)

if __name__ == "__main__":
    main()
