import streamlit as st
import pandas as pd
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
from datetime import datetime
import io
import json

st.set_page_config(
    page_title="Controle de Presença",
    layout="wide"
)

st.title("📋 Controle de Presença")

# Carregar credenciais via secrets (Cloud)
if "gcp_service_account" in st.secrets:
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    client = vision.ImageAnnotatorClient(credentials=credentials)
else:
    st.error("Credenciais não encontradas.")
    st.stop()

uploaded_image = st.file_uploader("📷 Envie a imagem da lista", type=["png", "jpg", "jpeg"])

if uploaded_image:

    image = Image.open(uploaded_image)
    st.image(image, use_column_width=True)

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    content = img_byte_arr.getvalue()

    vision_image = vision.Image(content=content)
    response = client.text_detection(image=vision_image)
    texts = response.text_annotations

    if not texts:
        st.warning("Nenhum texto detectado.")
    else:
        texto_total = texts[0].description
        linhas = texto_total.split("\n")

        nomes = []
        for linha in linhas:
            linha = linha.strip()
            if len(linha) > 5 and linha.isupper():
                if "NOME" not in linha and "PRODUTIVO" not in linha:
                    nomes.append(linha)

        nomes = list(dict.fromkeys(nomes))

        st.success(f"{len(nomes)} nomes detectados!")

        dados = []

        st.divider()
        st.subheader("Marcação")

        for nome in nomes:

            with st.container():
                col1, col2, col3, col4, col5 = st.columns([4,1,1,1,1])

                col1.write(nome)
                presente = col2.checkbox("Presente", value=True, key=f"p_{nome}")
                justificado = col3.checkbox("Just.", key=f"j_{nome}")
                atestado = col4.checkbox("Atest.", key=f"a_{nome}")
                pulmao = col5.checkbox("🫁", key=f"pl_{nome}")

                status = "PRESENTE"
                if pulmao:
                    status = "PULMAO"
                elif not presente:
                    status = "AUSENTE"

                dados.append({
                    "Nome": nome,
                    "Status": status,
                    "Justificado": justificado,
                    "Atestado": atestado
                })

        st.divider()

        if st.button("📄 Gerar Relatório"):

            hoje = datetime.now().strftime("%d/%m")
            titulo = f"ABS T2 ({hoje})\n"

            ausentes = []
            pulmoes = []

            for item in dados:
                if item["Status"] == "AUSENTE":
                    nome_txt = f"-{item['Nome']}"
                    if item["Justificado"]:
                        nome_txt += " (JUST)"
                    if item["Atestado"]:
                        nome_txt += " (ATEST)"
                    ausentes.append(nome_txt)

                if item["Status"] == "PULMAO":
                    pulmoes.append(f"-{item['Nome']}")

            abs_real = len(ausentes)

            resultado = titulo + "\n"

            if ausentes:
                resultado += "\n".join(ausentes) + "\n\n"

            if pulmoes:
                resultado += "PULMÕES 🫁\n"
                resultado += "\n".join(pulmoes) + "\n\n"

            resultado += f"ABS REAL: {abs_real}"

            st.text_area("📲 Copie para WhatsApp", resultado, height=300)
