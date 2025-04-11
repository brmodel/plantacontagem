import streamlit as st
import geopandas as gpd
import folium as fol
from streamlit_gsheets import GSheetsConnection
import requests
from streamlit_folium import st_folium
from folium.plugins import Search


# --- Constants ---
APP_TITLE = "Mapa das Unidades Produtivas"
APP_SUB_TITLE = "Filtro e visualização de dados no mapa"

# --- Load Data ---
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type="gheets")
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
    data = conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074")
    clean_data = data.dropna(subset=['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral']).copy()
    clean_data['Numeral'] = clean_data['Numeral'].astype(int)
    return clean_data

df = load_data()

# --- Search box ---
search_query = st.text_input("Buscar por Nome:", "").strip().lower()
if search_query:
    df = df[df['Nome'].str.lower().str.contains(search_query)]

# --- Create GeoJSON features ---
def df_to_geojson(dataframe: pd.DataFrame):
    features = []
    for _, row in dataframe.iterrows():
        popup_html = f"""
        <b>Nome:</b> {row['Nome']}<br>
        <b>Tipo:</b> {row['Tipo']}<br>
        <b>Regional:</b> {row['Regional']}<br>
        <b>Numeral:</b> {row['Numeral']}
        """
        feature = {
            "type": "Feature",
            "properties": {
                "popup": popup_html
            },
            "geometry": {
                "type": "Point",
                "coordinates": [row['lon'], row['lat']]
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }

geojson_data = df_to_geojson(df)

# --- Create Folium Map ---
m = fol.Map(location=[-19.9, -43.9], zoom_start=10, control_scale=True)

# Add all markers as a single GeoJson layer
marker_layer = fol.GeoJson(
    geojson_data,
    name='Unidades Produtivas',
    popup=fol.GeoJsonPopup(fields=["popup"], labels=False),
)
marker_layer.add_to(m)

# Add layer control
fol.LayerControl().add_to(m)

# --- Render ---
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_folium(m, width=1200, height=800)
