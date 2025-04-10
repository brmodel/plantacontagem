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

@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
    return conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074").dropna(subset=['Nome','lon','lat','Tipo','Regional','Numeral'])

@st.cache_data(ttl=3600, show_spinner=False)
def load_geojson():
    return requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json()

# Load data once
data_ups = load_data()
regionais_json = load_geojson()

# Create GeoDataFrame
gdf = gpd.GeoDataFrame(
    data_ups,
    geometry=gpd.points_from_xy(data_ups.lon, data_ups.lat)
)

# Create Base Map
m = fol.Map(location=[-19.88589, -44.07113], zoom_start=12.18, tiles="OpenStreetMap")

# Custom icon configuration
icon_config = {
    1: {'icon': 'leaf', 'color': 'green'},
    2: {'icon': 'home', 'color': 'blue'},
    3: {'icon': 'star', 'color': 'orange'},
    4: {'icon': 'shopping-cart', 'color': 'purple'}
}

# Create optimized marker layer
marker_layer = fol.FeatureGroup(name="Unidades Produtivas", show=True)

# Batch process markers using GeoJSON
fol.GeoJson(
    gdf.__geo_interface__,
    name="ProductionPoints",
    marker=fol.CircleMarker(radius=0),  # Dummy marker for initialization
    popup=fol.GeoJsonPopup(
        fields=["Nome", "Tipo", "Regional"],
        aliases=["", "", ""],
        localize=True,
        labels=False,
        style="width: 200px; font-family: Arial;",
        max_width=250
    ),
    tooltip=fol.GeoJsonTooltip(
        fields=["Nome"],
        aliases=["Unidade Produtiva: "],
        style="font-family: Arial; font-size: 12px;"
    ),
    point_to_layer=lambda feature, latlng: fol.Marker(
        latlng,
        icon=fol.Icon(
            icon=icon_config.get(feature['properties']['Numeral'], {}).get('icon', 'question'),
            color=icon_config.get(feature['properties']['Numeral'], {}).get('color', 'gray'),
            prefix='fa'
        )
    )
).add_to(marker_layer)

# Add regional boundaries
regionais_group = fol.FeatureGroup(name="Regionais", show=True)
fol.GeoJson(
    regionais_json,
    name="Regionais",
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
    tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"])
).add_to(regionais_group)

# Add layers to map
regionais_group.add_to(m)
marker_layer.add_to(m)

# Configure search once
Search(
    layer=marker_layer,
    search_label='Nome',
    position='topright',
    placeholder='Pesquisar UPs...',
    collapsed=True,  # Collapsed by default for cleaner UI
    search_zoom=16
).add_to(m)

# Add layer control
fol.LayerControl().add_to(m)

# Streamlit display
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(m, width=1200, height=800, key="main_map")
