import streamlit as st
import geopandas as gpd
import folium as fol
from streamlit_gsheets import GSheetsConnection
import requests
from streamlit_folium import st_folium
from folium.plugins import LocateControl, Search
import json
import pandas as pd

# Page Configuration
st.set_page_config(layout="wide")

APP_TITLE = 'Mapeamento da Agricultura Urbana em Contagem'
APP_SUB_TITLE = 'WebApp criado para identificar as Unidades Produtivas Ativas em parceria com a Prefeitura de Contagem'

# Cached Data Loading
@st.cache_data(ttl=3600)
def load_data():
    # Load Google Sheets data
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
    raw_data = conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074")
    
    # Clean data
    data_clean = raw_data.dropna(subset=['Nome','lon','lat','Tipo','Regional','Numeral'])
    data_clean["lon"] = pd.to_numeric(data_clean["lon"], errors="coerce")
    data_clean["lat"] = pd.to_numeric(data_clean["lat"], errors="coerce")
    data_clean = data_clean.dropna(subset=["lat", "lon"])
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(
        data_clean,
        geometry=gpd.points_from_xy(data_clean["lon"], data_clean["lat"])
    )
    gdf["Numeral"] = gdf["Numeral"].astype(int)
    
    # Load Regional GeoJSON
    geojson_url = "https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson"
    regionais = requests.get(geojson_url).json()
    
    return gdf, regionais

# Style Functions
def regional_style(feature):
    colors = {
        1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
        5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
    }
    return {
        "fillOpacity": 0.4,
        "fillColor": colors.get(feature["properties"].get("id", 0), "#fddaec"),
        "color": "black",
        "weight": 2,
        "dashArray": "5,5"
    }

# Map Creation
def create_map(gdf, regionais):
    m = fol.Map(
        location=[-19.88589, -44.07113],
        zoom_start=12.18,
        tiles="OpenStreetMap",
        crs='EPSG4326'
    )
    
    # Pre-serialize GeoJSON
    geojson_str = gdf.to_json()
    
    # Feature Group Configuration
    feature_groups = {
        1: {"name": "Unidade Produtiva Comunitária", "color": "green"},
        2: {"name": "Unidade Produtiva Institucional", "color": "blue"},
        3: {"name": "Unidade Produtiva Institucional/Comunitária", "color": "orange"},
        4: {"name": "Feira Comunitária", "color": "purple"}
    }
    
    # Add Production Units
    search_layers = []
    for numeral, config in feature_groups.items():
        fg = fol.FeatureGroup(name=config["name"])
        
        # Filter features
        data = json.loads(geojson_str)
        filtered = [f for f in data["features"] if f["properties"]["Numeral"] == numeral]
        
        # Capture color in loop scope
        layer_color = config["color"]
        fol.GeoJson(
            {"type": "FeatureCollection", "features": filtered},
            style_function=lambda x, color=layer_color: {
                "color": color,
                "fillColor": color
            },
            marker=fol.CircleMarker(radius=5, weight=2, fill_opacity=0.5),
            popup=fol.GeoJsonPopup(
                fields=["Nome", "Tipo", "Regional"],
                aliases=["Nome: ", "Tipo: ", "Regional: "],
                labels=True
            ),
            tooltip=fol.GeoJsonTooltip(
                fields=["Nome"],
                aliases=["Unidade Produtiva: "]
            )
        ).add_to(fg)
        
        fg.add_to(m)
        search_layers.append(fg)
    
    # Add Regional Boundaries
    fol.GeoJson(
        regionais,
        style_function=regional_style,
        tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
        name="Regionais"
    ).add_to(m)
    
    # Add Plugins
    Search(
        layer=search_layers,
        search_label="Nome",
        position="topright",
        placeholder="Pesquisar por Unidades Produtivas...",
        collapsed=False
    ).add_to(m)
    
    LocateControl().add_to(m)
    fol.LayerControl().add_to(m)
    
    return m  # Properly indented inside function

# Main Execution
gdf, regionais = load_data()
map_obj = create_map(gdf, regionais)

# Streamlit Display
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(map_obj, width=1200, height=800)
