import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker, plugins
from folium.plugins import LocateControl, FloatImage
import requests
import io
from PIL import Image
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# --- Config ---
APP_TITLE = "Planta Contagem"
APP_SUB_TITLE = "Mapa das Unidades Produtivas de Contagem"
APP_CAPTION = "Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF), em parceria com a Prefeitura Municipal de Contagem - MG"
ICON_BASE_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
ICON_MAPPING = {
    1: "leaf_green.png",
    2: "leaf_orange.png",
    3: "leaf_blue.png",
    4: "leaf_purple.png",
}
COLOR_MAPPING = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
    4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
    7: "#e5d8bd"
}
IMAGE_BANNER_URLS = [
    "ilustracao_pmc.png",
    "banner_pmc.png"
]
LOGO_PMC = "https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"
COMPASS_URL = "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/compass-rose.png"

# Precomputed URLs
ICON_URLS = {k: ICON_BASE_URL + v for k, v in ICON_MAPPING.items()}
DEFAULT_ICON = ICON_BASE_URL + "leaf_green.png"
BANNER_URLS = [ICON_BASE_URL + img for img in IMAGE_BANNER_URLS]

# HTML Templates
TOOLTIP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px">
    <p><b>Unidade Produtiva:<br>{}</b></p>
</div>
"""

POPUP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px; min-width: 200px;">
    <h6 style="margin: 0 0 5px 0;"><b>{}</b></h6>
    <p style="margin: 2px 0;"><b>Tipo:</b> {}</p>
    <p style="margin: 2px 0;"><b>Regional:</b> {}</p>
</div>
"""

# --- Load Data ---
@st.cache_data(ttl=600)
def load_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
        data = pd.read_csv(url, usecols=range(6))
        clean_data = data.dropna(subset=['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral']).copy()
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

# --- Map Creation ---
def create_geojson_image(geojson_data):
    """Convert GeoJSON to georeferenced image with legend"""
    gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
    
    # Create plot with embedded legend
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(
        ax=ax,
        column='Name',
        categorical=True,
        legend=True,
        legend_kwds={
            'loc': 'upper left',
            'bbox_to_anchor': (1, 1),
            'title': 'Regionais'
        },
        edgecolor='black',
        linewidth=0.5,
        cmap='Pastel1'
    )
    ax.axis('off')
    
    # Save to buffer
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150, transparent=True)
    img_buffer.seek(0)
    
    return np.array(Image.open(img_buffer)), gdf.total_bounds

def create_map(data, geojson_data):
    m = folium.Map(location=[-19.89323, -43.97145], 
                 tiles="OpenStreetMap", 
                 zoom_start=12.49, 
                 control_scale=True)

    # Add GeoJSON as image overlay
    try:
        img_array, bounds = create_geojson_image(geojson_data)
        folium.raster_layers.ImageOverlay(
            img_array,
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            opacity=0.5,
            interactive=False
        ).add_to(m)
    except Exception as e:
        st.error(f"Erro ao criar overlay: {e}")

    # Add wind rose
    FloatImage(
        COMPASS_URL,
        bottom=5,
        left=5,
        width=75,
        height=75,
        position='bottomleft'
    ).add_to(m)

    # Add markers
    for _, row in data.iterrows():
        icon_url = ICON_URLS.get(row["Numeral"], DEFAULT_ICON)
        icon = folium.CustomIcon(icon_url, icon_size=(32, 32), icon_anchor=(16, 16))
        
        Marker(
            location=[row["lat"], row["lon"]],
            popup=POPUP_TEMPLATE.format(row['Nome'], row['Tipo'], row['Regional']),
            icon=icon,
            tooltip=TOOLTIP_TEMPLATE.format(row['Nome'])
        ).add_to(m)

    # Add controls
    LocateControl().add_to(m)
    folium.LayerControl().add_to(m)

    return m

# --- Main App ---
def main():
    st.logo(LOGO_PMC, size="large", link="https://portal.contagem.mg.gov.br/")
    st.title(APP_TITLE)
    st.header(APP_SUB_TITLE)

    # Load data
    df = load_data()
    geojson_data = load_geojson()

    # Search functionality
    search_query = st.text_input("Pesquisar por Unidades Produtivas:", "").strip().lower()
    if search_query:
        filtered_df = df[df["Nome"].str.lower().str.contains(search_query, regex=False)]
        if filtered_df.empty:
            st.warning("Nenhuma unidade encontrada com esse nome")
    else:
        filtered_df = df

    # Display map
    if not df.empty:
        m = create_map(filtered_df, geojson_data)
        st_folium(m, width=1400, height=700)
    else:
        st.warning("Nenhum dado disponível para exibir")
    
    st.caption(APP_CAPTION)

    # Display banners
    for url in BANNER_URLS:
        st.image(url, use_container_width=True)

if __name__ == "__main__":
    main()
