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

# Custom icon configuration
icon_config = {
    1: {'icon': 'leaf', 'color': 'green', 'prefix': 'fa'},
    2: {'icon': 'home', 'color': 'blue', 'prefix': 'fa'},
    3: {'icon': 'star', 'color': 'orange', 'prefix': 'fa'},
    4: {'icon': 'shopping-cart', 'color': 'purple', 'prefix': 'fa'}
}

# Create feature group for markers
markers_group = fol.FeatureGroup(name="Unidades Produtivas", show=True)

# Add custom markers
for _, row in gdf.iterrows():
    numeral = row['Numeral']
    config = icon_config.get(numeral, {'icon': 'question', 'color': 'gray', 'prefix': 'fa'})
    
    # Create custom icon
    custom_icon = fol.Icon(
        icon=config['icon'],
        prefix=config['prefix'],
        color=config['color'],
        icon_color='white'
    )
    
    # Create HTML popup
    popup_html = f"""
    <div style="font-family: Arial; font-size: 14px; min-width: 200px;">
        <h6 style="margin: 0 0 5px 0; color: {config['color']};">{row['Nome']}</h6>
        <p style="margin: 2px 0;"><b>Tipo:</b> {row['Tipo']}</p>
        <p style="margin: 2px 0;"><b>Regional:</b> {row['Regional']}</p>
    </div>
    """
    
    # Create marker
    fol.Marker(
        location=(row['lat'], row['lon']),
        icon=custom_icon,
        popup=fol.Popup(popup_html, max_width=250),
        tooltip=f"Unidade Produtiva: {row['Nome']}"
    ).add_to(markers_group)

# Add regional boundaries
regionais_group = fol.FeatureGroup(name="Regionais", show=True)
fol.GeoJson(
    requests.get("https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson").json(),
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
markers_group.add_to(m)

# Add search functionality
Search(
    layer=markers_group,
    search_label='Nome',
    position='topright',
    placeholder='Pesquisar UPs...',
    collapsed=False,
    search_zoom=16
).add_to(m)

# Add layer control
fol.LayerControl().add_to(m)

# Streamlit display
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(m, width=1200, height=800)
