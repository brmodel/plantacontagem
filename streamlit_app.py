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

# Create styled GeoJSON layer with original marker appearance
all_points = fol.GeoJson(
    gdf.__geo_interface__,
    name="Todas as UPs",
    style_function=lambda x: {
        'fillColor': {1: 'green', 2: 'blue', 3: 'orange', 4: 'purple'}.get(
            x['properties']['Numeral'], 'gray'
        ),
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.7
    },
    marker=fol.CircleMarker(
        radius=8,
        weight=1,
        fill=True
    ),
    popup=fol.GeoJsonPopup(
        fields=["Nome", "Tipo", "Regional"],
        aliases=["", "", ""],
        localize=True,
        labels=False,
        style="width: 200px; font-family: Arial;",
        max_width=250,
        html="""
            <h6 style="margin-bottom:5px;"><b>{Nome}</b></h6>
            <p style="margin:2px 0;"><b>Tipo:</b> {Tipo}</p>
            <p style="margin:2px 0;"><b>Regional:</b> {Regional}</p>
        """
    ),
    tooltip=fol.GeoJsonTooltip(
        fields=["Nome"],
        aliases=["Unidade Produtiva: "],
        style="font-family: Arial; font-size: 12px;"
    )
).add_to(m)

# Add Regional Boundaries with original styling
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
        "fillOpacity": 0.4,
        "dashArray": "5,5"
    },
    tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"])
).add_to(m)

# Add Search Plugin
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
