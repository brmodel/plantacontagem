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

if 'map' not in st.session_state:
    data_ups = load_data()
    regionais_json = load_geojson()
    
    gdf = gpd.GeoDataFrame(
        data_ups,
        geometry=gpd.points_from_xy(data_ups.lon, data_ups.lat)
    )

    m = fol.Map(location=[-19.88589, -44.07113], zoom_start=12.18, tiles="OpenStreetMap")

    # Create individual GeoJSON layers for each numeral type
    numeral_layers = []
    numeral_config = {
        1: {'name': 'Comunitária', 'color': 'green'},
        2: {'name': 'Institucional', 'color': 'blue'},
        3: {'name': 'Híbrida', 'color': 'orange'},
        4: {'name': 'Feira', 'color': 'purple'}
    }

    for numeral, config in numeral_config.items():
        subset = gdf[gdf.Numeral == numeral]
        layer = fol.GeoJson(
            subset.__geo_interface__,
            name=config['name'],
            style_function=lambda x, c=config['color']: {
                'fillColor': c,
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
        )
        layer.add_to(m)
        numeral_layers.append(layer)

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

    # Configure search across all numeral layers
    Search(
        layer=numeral_layers,
        search_label='Nome',
        position='topright',
        placeholder='Pesquisar UPs...',
        collapsed=False,
        search_zoom=16
    ).add_to(m)

    fol.LayerControl().add_to(m)
    st.session_state.map = m

st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(st.session_state.map, width=1200, height=800)
