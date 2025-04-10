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

@st.cache_data(ttl=3600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
    data = conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074")
    return data.dropna(subset=['Nome','lon','lat','Tipo','Regional','Numeral'])

@st.cache_data(ttl=3600)
def load_geojson():
    return requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json()

# Initialize session state for map caching
if 'map' not in st.session_state:
    # Load data
    data_ups = load_data()
    regionais_json = load_geojson()
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(
        data_ups,
        geometry=gpd.points_from_xy(data_ups.lon, data_ups.lat)
    )

    # Create base map
    m = fol.Map(location=[-19.88589, -44.07113], zoom_start=12.18, tiles="OpenStreetMap")

    # Create numeral groups
    numeral_groups = {
        1: fol.FeatureGroup(name='Comunitária'),
        2: fol.FeatureGroup(name='Institucional'),
        3: fol.FeatureGroup(name='Híbrida'),
        4: fol.FeatureGroup(name='Feira')
    }

    # Add production points with numeral filtering
    for numeral, group in numeral_groups.items():
        subset = gdf[gdf.Numeral == numeral]
        fol.GeoJson(
            subset.__geo_interface__,
            name=group.layer_name,  # Corrected here
            style_function=lambda x, n=numeral: {
                'fillColor': {1: 'green', 2: 'blue', 3: 'orange', 4: 'purple'}[n],
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.7
            },
            marker=fol.CircleMarker(radius=8),
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
        ).add_to(group)
        group.add_to(m)

    # Add regional boundaries
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

    # Configure search across all numeral groups
    Search(
        layer=list(numeral_groups.values()),
        search_label='Nome',
        position='topright',
        placeholder='Pesquisar UPs...',
        collapsed=False,
        search_zoom=16
    ).add_to(m)

    # Add layer control
    fol.LayerControl().add_to(m)
    
    # Store in session state
    st.session_state.map = m

# Display cached map
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(st.session_state.map, width=1200, height=800)
