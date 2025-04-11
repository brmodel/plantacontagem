import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl

# --- Config ---
APP_TITLE = "Planta Contagem"
APP_SUB_TITLE = "Mapa das Unidades Produtivas de Contagem"
APP_CAPTION = "Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar - CMAUF, em parceria com a Prefeitura Municipal de Contagem - MG"
ICON_BASE_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
ICON_MAPPING = {
    1: "leaf_green.png",
    2: "leaf_orange.png",
    3: "leaf_blue.png",
    4: "leaf_purple.png",
}
IMAGE_BANNER_URLS = [
    "banner_pmc.png",
    "ilustracao_pmc.png"
]
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"

# --- Load Data ---
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
    data = pd.read_csv(url, usecols=range(6))
    clean_data = data.dropna(subset=['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral']).copy()
    clean_data['Numeral'] = clean_data['Numeral'].astype(int)
    return clean_data

@st.cache_data(ttl=3600)
def load_geojson():
    return requests.get(GEOJSON_URL).json()

df = load_data()
regionais_json = load_geojson()

# --- Create Folium Map ---
m = folium.Map(location=[-19.89323, -44.00145], tiles="CartoDB Positron", zoom_start=12.49, control_scale=True)

# Add GeoJSON layer under markers
folium.GeoJson(
    regionais_json,
    name='Regionais',
    style_function=lambda x: {
        "fillColor": {
            1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
            4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
            7: "#e5d8bd"
        }.get(x['properties'].get('id', 0), "#fddaec"),
        "color": "black",
        "weight": 2,
        "fillOpacity": 0.4,
        "dashArray": "5,5"
    },
    tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
    control=False
).add_to(m)

# Add markers on top of the geojson
for _, row in df.iterrows():
    numeral = row["Numeral"]
    icon_file = ICON_MAPPING.get(numeral, "leaf_green.png")

    icon_url = ICON_BASE_URL + icon_file
    icon = folium.CustomIcon(
        icon_url,
        icon_size=(32, 32),
        icon_anchor=(16, 16)
    )

    tooltip_content = f"""
    Conheça a Unidade Produtiva: {row['Nome']}
    """
    
    popup_content = f"""
    <b>{row['Nome']}</b><br>
    Tipo: {row['Tipo']}<br>
    Regional: {row['Regional']}<br>
    """
    Marker(
        location=[row["lat"], row["lon"]],
        popup=popup_content,
        icon=icon,
        tooltip=tooltip_content
    ).add_to(m)

folium.plugins.LocateControl().add_to(m)
folium.LayerControl().add_to(m)

# --- Layout ---
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)

# --- Search box ---
search_query = st.text_input("Pesquisar por Unidades Produtivas:", "").strip().lower()
if search_query:
    df = df[df["Nome"].str.lower().str.contains(search_query)]

# Display Map
st_data = st_folium(m, width=1200, height=700)
st.caption(APP_CAPTION)
st.image("https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true")

# Display banners
for img in IMAGE_BANNER_URLS:
    st.image(ICON_BASE_URL + img, use_container_width=False)
