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

# Create Feature Groups
feature_groups = {
    1: fol.FeatureGroup(name="Unidade Produtiva Comunitária"),
    2: fol.FeatureGroup(name="Unidade Produtiva Institucional"),
    3: fol.FeatureGroup(name="Unidade Produtiva Híbrida"),
    4: fol.FeatureGroup(name="Feira Comunitária")
}

# Add Markers to Feature Groups (Original Style)
for _, row in gdf.iterrows():
    numeral = row["Numeral"]
    color = {1: "green", 2: "blue", 3: "orange", 4: "purple"}.get(numeral, "gray")
    
    marker = fol.Marker(
        location=(row["lat"], row["lon"]),
        popup=fol.Popup(
            f"""<h6 style="margin-bottom:5px;"><b>{row['Nome']}</b></h6>
            <p style="margin:2px 0;"><b>Tipo:</b> {row['Tipo']}</p>
            <p style="margin:2px 0;"><b>Regional:</b> {row['Regional']}</p>""",
            max_width=250
        ),
        icon=fol.Icon(color=color),
        tooltip=row['Nome']
    )
    
    if numeral in feature_groups:
        marker.add_to(feature_groups[numeral])

# Add Regional Boundaries First (to ensure markers stay on top)
regionais = requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json()
fol.GeoJson(
    regionais,
    name="Regionais",
    style_function=lambda x: {
        "fillOpacity": 0.4,
        "fillColor": {
            1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
            4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
            7: "#e5d8bd"
        }.get(x['properties']['id'], "#fddaec"),
        "color": "black",
        "weight": 2,
        "dashArray": "5,5"
    },
    tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"])
).add_to(m)

# Add Feature Groups to Map
for fg in feature_groups.values():
    fg.add_to(m)

# Configure Search Plugin
Search(
    layer=list(feature_groups.values()),  # Pass FeatureGroups directly
    search_label='Nome',
    position='topright',
    placeholder='Pesquisar UPs...',
    collapsed=False,
    search_zoom=16
).add_to(m)

# Add Layer Control
fol.LayerControl().add_to(m)

# Streamlit Display
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(m, width=1200, height=800)
