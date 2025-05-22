# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl
import numpy as np
import json
import base64

# Textos
SAIBA_TITULO = "Conheça o CMAUF"
SAIBA_SUBTITULO = "Centro Municipal de Agricultura Urbana e Familiar"
SAIBA_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF)"

TEXTAO = """<div style="font-family: Arial, sans-serif; font-size: 12px; width: auto; word-break: break-word; padding: 8px;">
Criado pela Prefeitura Municipal de Contagem - MG, o CMAUF combate a insegurança alimentar e fortalece a agricultura sustentável, alinhado ao programa municipal <b>Contagem Sem Fome</b> e a políticas nacionais como o <b>Alimenta Cidades</b>. Sua atuação inclui:

<b>Capacitação e apoio técnico:</b> implanta e acompanha Unidades Produtivas (UPs) em todo o município, oferecendo formação, troca de mudas e compostos para subsidiar a produção.<br>
<b>Sistemas agroecológicos:</b> promove a comercialização direta de alimentos e tecnologias sociais, em sintonia com as Políticas Nacional e Estadual de Agricultura Urbana.<br>
<b>Mapeamento estratégico:</b> identifica demandas e oportunidades para ações concretas, desde produção de alimentos até criação de pequenos animais.<br>
O equipamento trabalha com quatro tipos de UPs:<br>
<b>Comunitárias</b>: gestão compartilhada em áreas públicas ou privadas;<br>
<b>Institucionais Públicas</b>: vinculadas a equipamentos como CRAS e centros de saúde;<br>
<b>Pedagógicas Escolares</b>: foco em educação ambiental e consumo saudável;<br>
<b>Territórios de Tradição</b>: quilombos, terreiros e comunidades tradicionais.<br>

Além disso, o CMAUF conta com uma parceria estratégica com a EMATER-MG, garantindo assistência a agricultores familiares do município, reforçando o compromisso com desenvolvimento sustentável e qualidade de vida.

Vinculado à Diretoria de Agricultura Urbana e Familiar (Subsecretaria SUSANA), o CMAUF transforma realidades locais, conectando campo e cidade através de práticas inovadoras.</div>""""

# Nomes base dos arquivos para os banners do rodapé (excluindo o logo da PMC por enquanto)
BANNER_PMC_BASE_FILENAMES_RODAPE = ["governo_federal.png", "alimenta_cidades.png", "contagem_sem_fome.png"]
LOGO_PMC_FILENAME = "banner_pmc.png" # Arquivo do logo da PMC, também usado como banner no rodapé

# Lista combinada de nomes de arquivos para os banners do rodapé
FOOTER_BANNER_FILENAMES = BANNER_PMC_BASE_FILENAMES_RODAPE + [LOGO_PMC_FILENAME]

# --- Funções de Cache de Imagem ---
@st.cache_data(show_spinner=False)
def get_image_as_base64(image_url: str) -> str | None:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        img_bytes = response.content
        content_type = response.headers.get('Content-Type', 'image/png')
        return f"data:{content_type};base64,{base64.b64encode(img_bytes).decode()}"
    except requests.exceptions.RequestException as e:
        print(f"Erro ao carregar imagem {image_url} como Base64: {e}")
        return None

@st.cache_data(show_spinner=False)
def get_image_bytes(image_url: str) -> bytes | None:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Erro ao carregar bytes da imagem {image_url}: {e}")
        return None

# URL para o logo da PMC no cabeçalho
LOGO_PMC_URL_CABEÇALHO = ICONES_URL_BASE + LOGO_PMC_FILENAME

# URLs para os banners do rodapé (agora incluindo o banner_pmc.png)
BANNER_PMC_URLS_RODAPE = [ICONES_URL_BASE + fname for fname in FOOTER_BANNER_FILENAMES]

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=SAIBA_TITULO, layout="wide", initial_sidebar_state="collapsed")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(APP_TITULO);
        st.header(APP_SUBTITULO)
    with col2:
        # Usa LOGO_PMC_URL_CABEÇALHO para o logo no cabeçalho
        logo_bytes = get_image_bytes(LOGO_PMC_URL_CABEÇALHO)
        if logo_bytes: st.image(logo_bytes, width=150)
        else: st.image(LOGO_PMC_URL_CABEÇALHO, width=150)

    st.markdown("---"); st.caption(SAIBA_DESC)

    # Defina a altura desejada para os banners do rodapé (em pixels)
    BANNER_RODAPE_HEIGHT_PX = 80 # Ajustado para um valor mais comum para banners de rodapé

    st.header(
    st.markdown(TEXTAO)

	

    def display_banner_html(url: str, height_px: int) -> str:
        """
        Gera o HTML para exibir um banner com altura fixa,
        alinhado e com aspect ratio preservado.
        Ajustado para ocupar a largura total do contêiner da coluna.
        """
        base64_image_data = get_image_as_base64(url)
        image_source = base64_image_data if base64_image_data else url

        return f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: {height_px}px;
            overflow: hidden;
            width: 100%; /* Garante que o contêiner flex ocupe toda a largura da coluna */
        ">
            <img src="{image_source}" alt="Banner" style="
                max-height: 100%;
                max-width: 100%; /* Garante que a imagem não ultrapasse a largura do contêiner */
                width: auto; /* Permite que a imagem ajuste sua largura mantendo a proporção */
                height: auto; /* Permite que a imagem ajuste sua altura mantendo a proporção */
                object-fit: contain;
                display: block;
            ">
        </div>
        """

    # Usa BANNER_PMC_URLS_RODAPE para os banners no rodapé
    if BANNER_PMC_URLS_RODAPE:
        # Define o número de colunas. Podemos usar 3 ou 4 para uma boa distribuição,
        # ou o número exato de banners se houver poucos, para evitar colunas vazias.
        # Max de colunas para evitar banners muito pequenos se houver muitos.
        num_banners = len(BANNER_PMC_URLS_RODAPE)
        num_cols = min(num_banners, 4) # Limita a no máximo 4 colunas para não ficar muito apertado

        # Cria as colunas com pesos iguais para distribuição uniforme
        cols_banner = st.columns(num_cols)

        for i, url in enumerate(BANNER_PMC_URLS_RODAPE):
            with cols_banner[i % num_cols]: # Usa o operador módulo para ciclar pelas colunas
                banner_html = display_banner_html(url, BANNER_RODAPE_HEIGHT_PX)
                st.markdown(banner_html, unsafe_allow_html=True)
