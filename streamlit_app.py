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

@st.cache_data
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
    data = conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074")
    return data.dropna(subset=['Nome','lon','lat','Tipo','Regional','Numeral'])

# Create GeoDataFrame
data_ups = load_data()
gdf = gpd.GeoDataFrame(
    data_ups,
    geometry=gpd.points_from_xy(data_ups.lon, data_ups.lat)
)

# Create Base Map
m = fol.Map(location=[-19.88589, -44.07113], zoom_start=12.18, tiles="OpenStreetMap")

# Create a single GeoJSON layer with all points
all_points = fol.GeoJson(
    gdf.__geo_interface__,
    name="Todas as UPs",
    style_function=lambda x: {
        'fillColor': {1: 'green', 2: 'blue', 3: 'orange', 4: 'purple'}.get(
            x['properties']['Numeral'], 'gray'
        ),
        'color': 'black',
        'radius': 5
    },
    marker=fol.CircleMarker(),
    popup=fol.GeoJsonPopup(fields=['Nome', 'Tipo', 'Regional', 'Numeral']),
    tooltip=fol.GeoJsonTooltip(fields=['Nome'])
).add_to(m)

# Add Regional Boundaries
regionais = requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json()
fol.GeoJson(
    regionais,
    name='Regionais',
    style_function=lambda x: {
        "fillColor": {
            1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
            4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
            7: "#e5d8bd"
        }.get(x['properties']['id'], "#fddaec"),
        "color": "black",
        "weight": 2,
        "fillOpacity": 0.4
    }
).add_to(m)

# Add Search Plugin to the single GeoJSON layer
Search(
    layer=all_points,
    search_label='Nome',
    position='topright',
    placeholder='Pesquisar UPs...',
    collapsed=False
).add_to(m)

# Add Layer Control
fol.LayerControl().add_to(m)

# Streamlit Display
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(m, width=1200, height=800)
