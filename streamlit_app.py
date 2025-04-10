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

# Create Feature Groups with original styling
feature_groups = {
    1: {"name": "Comunitária", "color": "green"},
    2: {"name": "Institucional", "color": "blue"},
    3: {"name": "Híbrida", "color": "orange"},
    4: {"name": "Feira", "color": "purple"}
}

search_layers = []

# Add regional boundaries first
regionais = requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json()
fol.GeoJson(
    regionais,
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
).add_to(m)

# Create production units with original styling
for numeral, config in feature_groups.items():
    fg = fol.FeatureGroup(name=f"UP {config['name']}")
    subset = gdf[gdf.Numeral == numeral]
    
    # Custom HTML popup
    popup_html = """
    <div style="font-family: Arial; font-size: 14px;">
        <h4 style="margin: 0; padding-bottom: 5px;"><b>{Nome}</b></h4>
        <p style="margin: 2px 0;"><b>Tipo:</b> {Tipo}</p>
        <p style="margin: 2px 0;"><b>Regional:</b> {Regional}</p>
    </div>
    """
    
    geojson = fol.GeoJson(
        subset.__geo_interface__,
        name=fg.layer_name,
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
            style="font-family: Arial; font-size: 12px;"
        )
    ).add_to(fg)
    
    fg.add_to(m)
    search_layers.append(geojson)

# Add search functionality
Search(
    layer=search_layers,
    search_label="Nome",
    position="topright",
    placeholder="Pesquisar UPs...",
    collapsed=False,
    search_zoom=16
).add_to(m)

# Add layer control
fol.LayerControl().add_to(m)

# Streamlit display
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(m, width=1200, height=800)
