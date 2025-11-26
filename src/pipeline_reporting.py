# src/pipeline_reporting.py
import os
from pathlib import Path
from email.message import EmailMessage
import smtplib

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]

# ---------------- VISUALIZACIONES EN JPG ---------------- #

def build_econometric_plots_jpg(panel_elast: pd.DataFrame) -> Path:
    out_dir = ROOT / "output" / "plots_econometricos"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Curva demanda (Precio vs Separaciones) por proyecto/tipología
    for (proj, tipo), g in panel_elast.groupby(["nombre_proyecto", "nombre_tipologia"]):
        if g["precio_lista"].nunique() < 2 or g["separaciones"].nunique() < 2:
            continue  # muy pocos datos para curva

        plt.figure(figsize=(7, 5))
        sns.scatterplot(x="precio_lista", y="separaciones", data=g)
        sns.regplot(x="precio_lista", y="separaciones", data=g,
                    scatter=False, line_kws={"linewidth": 2})
        plt.title(f"Demanda vs Precio – {proj} / {tipo}")
        plt.xlabel("Precio promedio (S/)")
        plt.ylabel("Separaciones")
        plt.tight_layout()

        # GUARDAR EN JPG
        fname = f"demand_curve_{proj}_{tipo}.jpg".replace(" ", "_")
        plt.savefig(out_dir / fname, dpi=200, format="jpg")
        plt.close()

    # 2) Boxplot de elasticidad
    plt.figure(figsize=(10, 6))
    sns.boxplot(x="nombre_proyecto", y="elasticidad", data=panel_elast)
    plt.xticks(rotation=45, ha="right")
    plt.title("Distribución de Elasticidad Precio-Demanda")
    plt.xlabel("Proyecto")
    plt.ylabel("Elasticidad")
    plt.tight_layout()

    box_fname = out_dir / "elasticidad_boxplot.jpg"
    plt.savefig(box_fname, dpi=200, format="jpg")
    plt.close()

    return out_dir

# ---------------- ENVÍO DE CORREO ---------------- #

def send_summary_email(attachments: list[Path]) -> None:
    user = os.environ["GMAIL_USER"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_addr = os.environ["GMAIL_TO"]

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to_addr
    msg["Subject"] = "Reporte econométrico de Pricing – Curva, Elasticidad y Forecast"

    msg.set_content(
        "Hola,\n\n"
        "Adjunto el paquete de reporting econométrico de pricing:\n"
        "- Curva de precios por piso con recomendaciones (subir/bajar/mantener).\n"
        "- Panel de elasticidad precio–cantidad.\n"
        "- Forecast de separaciones por proyecto/tipología.\n"
        "- Visualizaciones JPG de demanda y elasticidad.\n\n"
        "Enviado automáticamente por GitHub Actions.\n"
    )

    for path in attachments:
        if not path.exists():
            continue
        with path.open("rb") as f:
            data = f.read()

        # Detectar tipo básico por extensión
        suffix = path.suffix.lower()
        if suffix in [".jpg", ".jpeg"]:
            maintype, subtype = "image", "jpeg"
        elif suffix in [".xlsx"]:
            maintype = "application"
            subtype = "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            maintype, subtype = "application", "octet-stream"

        msg.add_attachment(
            data,
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, app_password)
        smtp.send_message(msg)

    print(f">>> [PIPELINE REPORTING] Correo enviado a {to_addr} con {len(attachments)} adjuntos.")

def main() -> None:
    print(">>> [PIPELINE REPORTING] Preparando archivos para el correo...")

    # 1) Cargar panel de elasticidad
    elast_path = ROOT / "output" / "elasticidad_panel.xlsx"
    panel_elast = pd.read_excel(elast_path)

    # 2) Generar visualizaciones en JPG
    print(">>> [PIPELINE REPORTING] Generando gráficos econométricos en JPG...")
    plots_dir = build_econometric_plots_jpg(panel_elast)

    # 3) Reunir adjuntos
    attachments: list[Path] = []

    # 3.1 Reporte de pricing
    pricing_report = ROOT / "output" / "pricing_curva_y_recomendaciones.xlsx"
    attachments.append(pricing_report)

    # 3.2 Panel elasticidad
    attachments.append(elast_path)

    # 3.3 Forecasts (todos los forecast_*.xlsx)
    for f in (ROOT / "output").glob("forecast_*.xlsx"):
        attachments.append(f)

    # 3.4 Todas las imágenes JPG
    for img in plots_dir.glob("*.jpg"):
        attachments.append(img)

    # 4) Enviar email
    print(f">>> [PIPELINE REPORTING] Adjuntando {len(attachments)} archivos...")
    send_summary_email(attachments)

if __name__ == "__main__":
    main()
