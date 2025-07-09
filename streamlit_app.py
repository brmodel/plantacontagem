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

# --- Configurações ---
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
APP_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF)"
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/icones/"
BANNER_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/"
PMC_PORTAL_URL = "https://portal.contagem.mg.gov.br"

ICON_DEFINITIONS = {
    1: {"file": "leaf_green.png", "label": "Comunitária"},
    2: {"file": "leaf_blue.png", "label": "Institucional"},
    3: {"file": "leaf_orange.png", "label": "Comunitária/Institucional"},
    4: {"file": "feira_cidade.png", "label": "Feira da Cidade"},
    5: {"file": "banco_alimentos.png", "label": "Banco de Alimentos"},
    6: {"file": "restaurante_pop.png", "label": "Restaurante Popular"},
    9: {"file": "sede_cmauf.png", "label": "Sede CMAUF"}
}
ICONE_PADRAO_FILENAME = "leaf_green.png"

MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
    5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
}

BANNER_PMC_BASE_FILENAMES_RODAPE = ["governo_federal.png", "alimenta_cidades.png", "contagem_sem_fome.png"]
LOGO_PMC_FILENAME = "banner_pmc.png"
FOOTER_BANNER_FILENAMES = BANNER_PMC_BASE_FILENAMES_RODAPE + [LOGO_PMC_FILENAME]
LAST_TWO_FOOTER_BANNERS = ["contagem_sem_fome.png", "banner_pmc.png"]
OFFSET_LOGO_PX = 40

GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"
MAX_POPOVER_INFO_CHARS = 250

CENTRO_INICIAL_MAPA = [-19.8888, -44.0535]
ZOOM_INICIAL_MAPA = 12
ZOOM_SELECIONADO_MAPA = 16

NORMAL_BANNER_SCALE = 1.0

# --- Funções de Cache de Imagem ---
@st.cache_data(show_spinner=False)
def get_image_as_base64(image_url: str) -> str | None:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        img_bytes = response.content
        if not img_bytes:
            print(f"Erro: Conteúdo da imagem vazio para {image_url}")
            return None
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

# --- URLs e Rótulos Pré-calculados ---
ICONE_LEGENDA = {key: props["label"] for key, props in ICON_DEFINITIONS.items()}
ICONE_PADRAO_URL = ICONES_URL_BASE + ICONE_PADRAO_FILENAME
LOGO_PMC_URL_CABEÇALHO = BANNER_URL_BASE + LOGO_PMC_FILENAME
BANNER_PMC_URLS_RODAPE = [BANNER_URL_BASE + fname for fname in FOOTER_BANNER_FILENAMES]

# --- Templates HTML ---
POPUP_TEMPLATE_BASE = """
<div style="font-family: Arial, sans-serif; font-size: 12px; width: auto; max-width: min(90vw, 466px); min-width: 200px; word-break: break-word; box-sizing: border-box; padding: 8px;">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{}</b></h6>
    <p style="margin: 4px 0;"><b>Tipo:</b> {}</p>
    <p style="margin: 4px 0;"><b>Regional:</b> {}</p>
    {} </div>"""
TOOLTIP_TEMPLATE = """<div style="font-family: Arial, sans-serif; font-size: 14px"><p><b>{}:</b><br>{}</p></div>"""

# --- Funções de Carregamento de Dados ---
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1qNmwcOhFnWrFHDYwkq36gHmk4Rx97b6RM0VqU94vOro/export?format=csv&gid=1832051074"
    try:
        data = pd.read_csv(url, usecols=range(8))
        
        # Convert columns to appropriate types
        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')
        
        # Drop rows with missing coordinates or numeral
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True)
        
        # Convert numeral to integer
        data['Numeral'] = data['Numeral'].astype('Int64')
        
        # Clean text columns
        for col in ['Nome', 'Tipo', 'Regional', 'Info', 'Instagram']:
            if col in data.columns:
                data[col] = data[col].astype(str).replace('nan', '', regex=False).replace('<NA>', '', regex=False)
        
        return data
    except pd.errors.EmptyDataError: 
        st.error("Erro: A planilha parece estar vazia ou sem cabeçalhos.")
        return pd.DataFrame()
    except ValueError as e: 
        st.error(f"Erro ao processar colunas: {e}. Verifique se os dados estão no formato esperado.")
        return pd.DataFrame()
    except Exception as e: 
        st.error(f"Erro inesperado ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    default_geojson = {"type": "FeatureCollection", "features": []}
    try:
        response = requests.get(GEOJSON_URL, timeout=20)
        response.raise_for_status()
        geojson_data = response.json()
        if not isinstance(geojson_data, dict) or "features" not in geojson_data:
            st.warning("Estrutura do GeoJSON inválida.")
            return default_geojson
        return geojson_data
    except requests.exceptions.Timeout:
        st.error(f"Timeout ao carregar GeoJSON: {GEOJSON_URL}")
        return default_geojson
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de rede ao carregar GeoJSON: {e}")
        return default_geojson
    except ValueError as e:
        st.error(f"Erro ao decodificar GeoJSON: {e}")
        return default_geojson
    except Exception as e:
        st.error(f"Erro inesperado ao carregar GeoJSON: {e}")
        return default_geojson

# [Rest of the code remains exactly the same as in your latest version...]
# Continue with all the existing functions: criar_legenda, criar_mapa, etc.
# The main() function and all other components should stay identical

def main():
    # [Keep the entire main() function exactly as is in your latest version]
    # Only the data loading URL has been changed in the load_data() function

if __name__ == "__main__":
    main()
