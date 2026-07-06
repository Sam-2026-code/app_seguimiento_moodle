import os
import io
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from moodle_client import MoodleClient

load_dotenv()

MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")

st.set_page_config(page_title="Seguimiento Moodle", layout="centered")

st.title("Seguimiento de alumnos en Moodle")

if not MOODLE_URL or not MOODLE_TOKEN:
    st.error("No se encontró la configuración de Moodle. Creá un archivo `.env` con:\n\n"
             "MOODLE_URL=https://tusitio.com/moodle\nMOODLE_TOKEN=tu-token")
    st.stop()

client = MoodleClient(MOODLE_URL, MOODLE_TOKEN)

uploaded_file = st.file_uploader(
    "Subí el archivo CSV de alumnos",
    type="csv",
    help="Formato: nombre;apellido;email;dni (separado por punto y coma)",
)

if uploaded_file is not None:
    df_input = pd.read_csv(uploaded_file, sep=";", header=0, dtype=str, encoding="latin1").fillna("")
    total_filas = len(df_input)
    st.caption(f"Filas en el archivo: {total_filas} (las filas vacías se omiten al procesar)")

    if st.button("Ejecutar seguimiento", type="primary"):
        bar = st.progress(0, text="Iniciando...")
        status = st.empty()

        total = 0
        resultados = []

        for update in client.process_csv(df_input):
            if update["tipo"] == "inicio":
                total = update["total"]
            elif update["tipo"] == "status":
                status.info(update["mensaje"])
                procesados = update.get("procesados", 0)
                bar.progress(
                    min(procesados / max(total, 1), 1.0),
                    text=f"Procesando alumno {procesados} de {total}",
                )
            elif update["tipo"] == "completo":
                resultados = update["rows"]

        if resultados:
            df_out = pd.DataFrame(resultados)

            st.success(f"Reporte generado: {len(df_out)} registros")
            st.dataframe(df_out, use_container_width=True, hide_index=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_out.to_excel(writer, index=False, sheet_name="Reporte")
            output.seek(0)

            st.download_button(
                label="Descargar Excel",
                data=output,
                file_name="reporte_seguimiento.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.warning("No se generaron resultados.")
else:
    st.info("Subí un archivo CSV para comenzar.")
