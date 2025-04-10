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

# GeoDataFrame Creation
gdf_ups = gpd.GeoDataFrame(
    data_ups,
    geometry=gpd.points_from_xy(data_ups["lon"], data_ups["lat"])
)

# Regional GeoJSON
regionais_json = requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json()

# Map Creation
contagem_base = fol.Map(location=[-19.88589, -44.07113], zoom_start=12.18, tiles="OpenStreetMap", max_zoom=20)

# Feature Groups
feature_groups = {
    1: fol.FeatureGroup(name="Unidade Produtiva Comunitária"),
    2: fol.FeatureGroup(name="Unidade Produtiva Institucional"),
    3: fol.FeatureGroup(name="Unidade Produtiva Institucional/Comunitária"),
    4: fol.FeatureGroup(name="Feira Comunitária")
}

# Add Markers to Feature Groups
for _, row in gdf_ups.iterrows():
    coord = (row["lat"], row["lon"])
    numeral = row["Numeral"]
    color = {1: "green", 2: "blue", 3: "orange"}.get(numeral, "purple")
    
    marker = fol.Marker(
        location=coord,
        popup=fol.Popup(f"<b>{row['Nome']}</b><br>Tipo: {row['Tipo']}<br>Regional: {row['Regional']}"),
        icon=fol.Icon(color=color),
        tooltip=row['Nome']
    )
    
    if numeral in feature_groups:
        marker.add_to(feature_groups[numeral])

# Add All Elements to Map
fol.GeoJson(
    regionais_json,
    style_function=lambda feature: {
        "fillOpacity": 0.4,
        "fillColor": {
            1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
            4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
            7: "#e5d8bd"
        }.get(feature["properties"].get("id", 0), "#fddaec"),
        "color": "black",
        "weight": 2,
        "dashArray": "5,5"
    },
    tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"])
).add_to(contagem_base)

for fg in feature_groups.values():
    fg.add_to(contagem_base)

# Add Search Functionality
search = Search(
    layer=list(feature_groups.values()),
    search_label="Nome",
    position="topright",
    placeholder="Pesquisar UPs...",
    collapsed=False
).add_to(contagem_base)

fol.LayerControl().add_to(contagem_base)

# Streamlit Display
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(contagem_base, width=1200, height=800)
