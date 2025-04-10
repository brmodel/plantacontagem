import streamlit as st
import geopandas as gpd
import folium as fol
from streamlit_gsheets import GSheetsConnection
import requests
from streamlit_folium import st_folium
from folium.plugins import LocateControl, Search
import pandas as pd

# Page Configuration
st.set_page_config(layout="wide")

APP_TITLE = 'Mapeamento da Agricultura Urbana em Contagem'
APP_SUB_TITLE = 'WebApp criado para identificar as Unidades Produtivas Ativas em parceria com a Prefeitura de Contagem'

@st.cache_data(ttl=3600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
    raw_data = conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074")
    
    # Data cleaning
    data_clean = raw_data.dropna(subset=['Nome','lon','lat','Tipo','Regional','Numeral'])
    data_clean["lon"] = pd.to_numeric(data_clean["lon"], errors="coerce")
    data_clean["lat"] = pd.to_numeric(data_clean["lat"], errors="coerce")
    data_clean = data_clean.dropna(subset=["lat", "lon"])
    
    # GeoDataFrame
    gdf = gpd.GeoDataFrame(
        data_clean,
        geometry=gpd.points_from_xy(data_clean["lon"], data_clean["lat"])
    )
    gdf["Numeral"] = gdf["Numeral"].astype(int)
    
    # Regional boundaries
    geojson_url = "https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson"
    regionais = requests.get(geojson_url).json()
    
    return gdf, regionais

def create_map(gdf, regionais):
    m = fol.Map(
        location=[-19.88589, -44.07113],
        zoom_start=12.18,
        tiles="OpenStreetMap",
        crs='EPSG4326'
    )
    
    # Create individual GeoJSON layers
    layers = {
        1: {"name": "Comunitária", "color": "green"},
        2: {"name": "Institucional", "color": "blue"},
        3: {"name": "Híbrida", "color": "orange"},
        4: {"name": "Feira", "color": "purple"}
    }
    
    search_layers = []
    
    for numeral, config in layers.items():
        layer_name = f"UP {config['name']}"
        subset = gdf[gdf["Numeral"] == numeral]
        
        # Create GeoJSON layer
        geojson_layer = fol.GeoJson(
            subset.__geo_interface__,
            name=layer_name,
            style_function=lambda x, c=config["color"]: {
                "color": c,
                "fillColor": c
            },
            marker=fol.CircleMarker(radius=5, weight=2, fill_opacity=0.5),
            popup=fol.GeoJsonPopup(fields=["Nome", "Tipo", "Regional"]),
            tooltip=fol.GeoJsonTooltip(fields=["Nome"])
        ).add_to(m)
        
        search_layers.append(geojson_layer)
        st.write(f"Created layer: {layer_name}")  # Debug output

    # Add regional boundaries
    fol.GeoJson(
        regionais,
        name="Regionais",
        style_function=lambda x: {
            "fillOpacity": 0.4,
            "fillColor": {
                1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
                4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
                7: "#e5d8bd"
            }.get(x["properties"].get("id", 0), "#fddaec"),
            "color": "black",
            "weight": 2,
            "dashArray": "5,5"
        },
        tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"])
    ).add_to(m)

    # Add search plugin
    st.write("Search layers types:", [type(l) for l in search_layers])  # Debug
    Search(
        layer=search_layers,
        search_label="Nome",
        position="topright",
        placeholder="Pesquisar por Unidades Produtivas...",
        collapsed=False
    ).add_to(m)
    
    # Add controls
    LocateControl().add_to(m)
    fol.LayerControl().add_to(m)
    
    return m

# Main execution
gdf, regionais = load_data()
map_obj = create_map(gdf, regionais)

# Streamlit interface
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(map_obj, width=1200, height=800)
