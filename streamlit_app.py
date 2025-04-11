import streamlit as st
import geopandas as gpd
import folium as fol
from streamlit_gsheets import GSheetsConnection
import requests
from streamlit_folium import st_folium
from folium.plugins import Search
import json

# Page config
st.set_page_config(layout="wide")
APP_TITLE = 'Mapeamento da Agricultura Urbana em Contagem'
APP_SUB_TITLE = 'WebApp criado para identificar as Unidades Produtivas Ativas em parceria com a Prefeitura de Contagem'

# Load FontAwesome
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">', unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
    data = conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074")
    clean_data = data.dropna(subset=['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral']).copy()
    clean_data['Numeral'] = clean_data['Numeral'].astype(int)
    return clean_data

@st.cache_data(ttl=3600)
def load_geojson():
    return requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json()

# Marker icon mapping
numeral_config = {
    1: {'name': 'Comunitária', 'color': 'green', 'icon': 'leaf'},
    2: {'name': 'Institucional', 'color': 'blue', 'icon': 'university'},
    3: {'name': 'Híbrida', 'color': 'orange', 'icon': 'tree'},
    4: {'name': 'Feira', 'color': 'purple', 'icon': 'shopping-cart'}
}

# Start app logic
if 'map' not in st.session_state:
    data_ups = load_data()
    regionais_json = load_geojson()

    gdf = gpd.GeoDataFrame(
        data_ups,
        geometry=gpd.points_from_xy(data_ups.lon, data_ups.lat),
        crs="EPSG:4326"
    )

    # Convert to GeoJSON with custom popup and config
    geojson_data = json.loads(gdf.to_json())
    for f in geojson_data["features"]:
        numeral = f["properties"]["Numeral"]
        icon_data = numeral_config.get(numeral, {})
        f["properties"]["popup_html"] = (
            f"<h6 style='margin-bottom:5px;'><b>{f['properties']['Nome']}</b></h6>"
            f"<p style='margin:2px 0;'><b>Tipo:</b> {f['properties']['Tipo']}</p>"
            f"<p style='margin:2px 0;'><b>Regional:</b> {f['properties']['Regional']}</p>"
        )
        f["properties"]["icon"] = icon_data.get("icon", "info-sign")
        f["properties"]["color"] = icon_data.get("color", "gray")

    m = fol.Map(location=[-19.88589, -44.07113], zoom_start=12.2, tiles="OpenStreetMap")

    # Add boundaries
    fol.GeoJson(
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
        tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"])
    ).add_to(m)

    # Add points as a single GeoJson layer using pointToLayer
    marker_layer = fol.GeoJson(
        geojson_data,
        name="Unidades Produtivas",
        popup=fol.GeoJsonPopup(fields=["popup_html"], labels=False, max_width=300),
        tooltip=fol.GeoJsonTooltip(fields=["Nome"]),
        point_to_layer=lambda feature, latlng: fol.Marker(
            location=latlng,
            icon=fol.Icon(
                icon=feature['properties'].get("icon", "info-sign"),
                color=feature['properties'].get("color", "gray"),
                prefix="fa"
            )
        )
    ).add_to(m)

    # Search plugin (works on GeoJson layer)
    Search(
        layer=marker_layer,
        search_label="Nome",
        position="topright",
        placeholder="Pesquisar UPs...",
        collapsed
