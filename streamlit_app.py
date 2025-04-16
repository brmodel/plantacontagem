import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl

# Configurações
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
APP_DESC = "Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF), em parceria com a Prefeitura Municipal de Contagem - MG"
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
ICONES = {
    1: "leaf_green.png",
    2: "leaf_orange.png",
    3: "leaf_blue.png",
    4: "leaf_purple.png",
}
MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
    4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
    7: "#e5d8bd"
}
BANNER_PMC_BASE = [
    "ilustracao_pmc.png",
    "banner_pmc.png"
]
LOGO_PMC = "https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"

# Precomputed URLs
ICONES_URL = {k: ICONES_URL_BASE + v for k, v in ICONES.items()}
ICONE_PADRAO = ICONES_URL_BASE + "leaf_green.png"
BANNER_PMC = [ICONES_URL_BASE + img for img in BANNER_PMC_BASE]

# Template para estilização HTML do Tooltip
TOOLTIP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px">
    <p><b>Unidade Produtiva:<br>{}</b></p>
</div>
"""

# Template para o CONTEÚDO HTML do Popup (COM O SCRIPT INLINE)
POPUP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px; min-width: 200px;">
    <h6 style="margin: 0 0 5px 0;"><b>{0}</b></h6>
    <p style="margin: 2px 0;"><b>Tipo:</b> {1}</p>
    <p style="margin: 2px 0;"><b>Regional:</b> {2}</p>
    <div class="texto-curto" id="texto-curto-{3}">
        {4}
    </div>
    <div class="texto-completo" id="texto-completo-{3}" style="display: none;">
        {5}
    </div>
    <button class="leia-mais-btn" onclick="toggleTexto('texto-curto-{3}', 'texto-completo-{3}', this)">Saiba Mais</button>
</div>
<style>
.texto-completo {{
    margin-top: 5px;
}}
.leia-mais-btn {{
    background: none;
    border: none;
    color: blue;
    cursor: pointer;
    padding: 0;
    font-size: 12px;
}}
.leia-mais-btn:hover {{
    text-decoration: underline;
}}
</style>
<script>
function toggleTexto(idCurto, idCompleto, botao) {{
    var elementoCurto = document.getElementById(idCurto);
    var elementoCompleto = document.getElementById(idCompleto);
    if (elementoCompleto.style.display === "none") {{
        elementoCurto.style.display = "none";
        elementoCompleto.style.display = "block";
        botao.textContent = "Mostrar Menos";
    }} else {{
        elementoCurto.style.display = "block";
        elementoCompleto.style.display = "none";
        botao.textContent = "Saiba Mais";
    }}
}}
</script>
"""

# Carregar Database e GeoJSON em paralelo
@st.cache_data(ttl=600)
def load_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
        data = pd.read_csv(url, usecols=range(7))
        clean_data = data.dropna(subset=['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral', 'Info']).copy()
        clean_data['Numeral'] = clean_data['Numeral'].astype(int)
        return clean_data
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    try:
        response = requests.get(GEOJSON_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}

# Criação do Mapa
def criar_legenda(geojson_data):
    """Cria legendas nos GEOJSONs"""
    regions = []
    for feature in geojson_data.get('features', []):
        props = feature.get('properties', {})
        regions.append({
            'id': props.get('id'),
            'name': props.get('Name')
        })

    items_legenda = []
    for region in sorted(regions, key=lambda x: x['id']):
        color = MAPEAMENTO_CORES.get(region['id'], "#fddaec")
        items_legenda.append(f"""
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="background: {color}; width: 20px; height: 20px; margin-right: 5px;"></div>
                <span>{region['name']}</span>
            </div>
        """)

    return folium.Element(f"""
        <div style="
            position: fixed;
            bottom: 50px;
            right: 20px;
            z-index: 1000;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px
