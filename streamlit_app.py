import streamlit as st
import geopandas as gpd
import folium as fol
from streamlit_gsheets import GSheetsConnection
import requests
from streamlit_folium import st_folium
from folium.plugins import Search
from folium import FeatureGroup, LayerControl, Icon, Marker, Popup, GeoJson, Map
from folium.map import Tooltip

# Page Configuration MUST BE FIRST
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

# Main logic
if 'map' not in st.session_state:
    data_ups = load_data()
    regionais_json = load_geojson()

    gdf = gpd.GeoDataFrame(
        data_ups,
        geometry=gpd.points_from_xy(data_ups.lon, data_ups.lat)
    )

    # Create folium map and attach to a Figure
    m = Map(location=[-19.88589, -44.07113], zoom_start=12.18, tiles="OpenStreetMap")
    figure = fol.Figure().add_child(m)

    all_markers_group = FeatureGroup(name="Todas UPs", show=True)
    all_markers_group.add_to(m)

    numeral_config = {
        1: {'name': 'Comunitária', 'color': 'green', 'icon': 'leaf'},
        2: {'name': 'Institucional', 'color': 'blue', 'icon': 'university'},
        3: {'name': 'Híbrida', 'color': 'orange', 'icon': 'tree'},
        4: {'name': 'Feira', 'color': 'purple', 'icon': 'shopping-cart'}
    }

    for numeral, config in numeral_config.items():
        subset = gdf[gdf.Numeral == numeral]
        group = FeatureGroup(name=config['name'])
        group.add_to(m)

        for _, row in subset.iterrows():
            marker = Marker(
                location=[row.lat, row.lon],
                icon=Icon(
                    icon=config['icon'],
                    prefix='fa',
                    color=config['color']
                ),
                popup=Popup(html=f"""
                    <h6 style="margin-bottom:5px;"><b>{row.Nome}</b></h6>
                    <p style="margin:2px 0;"><b>Tipo:</b> {row.Tipo}</p>
                    <p style="margin:2px 0;"><b>Regional:</b> {row.Regional}</p>
                """, max_width=250),
                tooltip=Tooltip(row.Nome)
            )
            marker.add_to(group)
            marker.add_to(all_markers_group)

    # Add regional GeoJson layer
    GeoJson(
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

    # Add Search functionality
    Search(
        layer=all_markers_group,
        search_label='tooltip',
        position='topright',
        placeholder='Pesquisar UPs...',
        collapsed=False,
        search_zoom=16
    ).add_to(m)

    LayerControl(collapsed=False).add_to(m)
    st.session_state.map = m

# Display Streamlit App
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(st.session_state.map, width=1200, height=800)
