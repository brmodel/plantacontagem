import streamlit as st
import geopandas as gpd
import folium as fol
from streamlit_gsheets import GSheetsConnection
import requests
from streamlit_folium import st_folium
from folium.plugins import Search

# Page Configuration
st.set_page_config(layout="wide")

APP_TITLE = 'Mapeamento da Agricultura Urbana em Contagem'
APP_SUB_TITLE = 'WebApp criado para identificar as Unidades Produtivas Ativas em parceria com a Prefeitura de Contagem'

# Data Loading
conn = st.connection("gsheets", type=GSheetsConnection)
url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
data_ups = conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074").dropna(subset=['Nome','lon','lat','Tipo','Regional','Numeral'])

# Create GeoDataFrame
gdf = gpd.GeoDataFrame(
    data_ups,
    geometry=gpd.points_from_xy(data_ups["lon"], data_ups["lat"])
)

# Regional GeoJSON
regionais_json = requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json()

# Create Base Map
m = fol.Map(location=[-19.88589, -44.07113], zoom_start=12.18, tiles="OpenStreetMap", max_zoom=20)

# Style Functions
def regional_style(feature):
    colors = {
        1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
        4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
        7: "#e5d8bd"
    }
    return {
        "fillOpacity": 0.4,
        "fillColor": colors.get(feature["properties"].get("id", 0), "#fddaec"),
        "color": "black",
        "weight": 2,
        "dashArray": "5,5"
    }

# Create Feature Groups with GeoJSON layers
feature_groups = {
    1: {"name": "Unidade Produtiva Comunitária", "color": "green"},
    2: {"name": "Unidade Produtiva Institucional", "color": "blue"},
    3: {"name": "Unidade Produtiva Institucional/Comunitária", "color": "orange"},
    4: {"name": "Feira Comunitária", "color": "purple"}
}

# Add regional boundaries first
fol.GeoJson(
    regionais_json,
    style_function=regional_style,
    tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
    name="Regionais",
    overlay=True
).add_to(m)

# Create search layer list
search_layers = []

for numeral, config in feature_groups.items():
    fg = fol.FeatureGroup(name=config["name"])
    subset = gdf[gdf["Numeral"] == numeral]
    
    # Create custom HTML popup
    popup_html = """
    <h6 style="margin-bottom: 5px;"><b>{Nome}</b></h6>
    <p style="margin: 2px 0;"><b>Tipo:</b> {Tipo}</p>
    <p style="margin: 2px 0;"><b>Regional:</b> {Regional}</p>
    """
    
    # Create GeoJSON layer with marker styling
    geojson = fol.GeoJson(
        subset.__geo_interface__,
        name=config["name"],
        style_function=lambda x: {"color": "transparent", "fillColor": "transparent"},
        marker=fol.CircleMarker(
            radius=8,
            weight=1,
            color=config["color"],
            fill_color=config["color"],
            fill_opacity=0.7
        ),
        popup=fol.GeoJsonPopup(
            fields=["Nome", "Tipo", "Regional"],
            aliases=["", "", ""],
            localize=True,
            labels=False,
            style="width: 200px;",
            max_width=250,
            html=popup_html
        ),
        tooltip=fol.GeoJsonTooltip(
            fields=["Nome"],
            aliases=["Unidade Produtiva: "],
            style=("font-family: Arial; font-size: 12px;")
        )
    )
    
    geojson.add_to(fg)
    fg.add_to(m)
    search_layers.append(geojson)

# Add Search plugin
Search(
    layer=search_layers,
    search_label="Nome",
    position="topright",
    placeholder="Pesquisar UPs...",
    collapsed=False,
    search_zoom=16
).add_to(m)

# Add Layer Control
fol.LayerControl().add_to(m)

# Streamlit Display
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(m, width=1200, height=800)
