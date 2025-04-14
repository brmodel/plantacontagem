import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl

# --- Config (static, runs once) ---
APP_TITLE = "Planta Contagem"
APP_SUB_TITLE = "Mapa das Unidades Produtivas de Contagem"
APP_CAPTION = "Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF), em parceria com a Prefeitura Municipal de Contagem - MG"
ICON_BASE_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
ICON_MAPPING = {
    1: "leaf_green.png",
    2: "leaf_orange.png",
    3: "leaf_blue.png",
    4: "leaf_purple.png",
}
COLOR_MAPPING = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
    4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
    7: "#e5d8bd"
}
IMAGE_BANNER_URLS = [
    "ilustracao_pmc.png",
    "banner_pmc.png"
]
LOGO_PMC = "https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"

# Precomputed URLs (static)
ICON_URLS = {k: ICON_BASE_URL + v for k, v in ICON_MAPPING.items()}
DEFAULT_ICON = ICON_BASE_URL + "leaf_green.png"
BANNER_URLS = [ICON_BASE_URL + img for img in IMAGE_BANNER_URLS]

# HTML Templates (static)
TOOLTIP_TEMPLATE = """..."""  # Keep your existing template
POPUP_TEMPLATE = """..."""    # Keep your existing template

# --- Cached Data Loaders ---
@st.cache_data(ttl=600)
def load_data():
    # Your existing load_data implementation
    pass

@st.cache_data(ttl=3600)
def load_geojson():
    # Your existing load_geojson implementation
    pass

# --- Map Components (cached) ---
@st.cache_data(ttl=3600, show_spinner=False)
def create_base_map(geojson_data):
    """Create static map components that don't change with search"""
    m = folium.Map(location=[-19.89323, -43.97145], 
                 tiles="OpenStreetMap", 
                 zoom_start=12.49, 
                 control_scale=True)
    
    folium.GeoJson(
        geojson_data,
        name='Regionais',
        style_function=lambda x: {
            "fillColor": COLOR_MAPPING.get(x['properties'].get('id'), "#fddaec"),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.3,
            "dashArray": "5,5"
        },
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
        interactive=False,
        control=False
    ).add_to(m)
    
    LocateControl().add_to(m)
    folium.LayerControl().add_to(m)
    
    return m

def create_legend(geojson_data):
    # Your existing create_legend implementation
    pass

# --- Main App Logic ---
def main_app():
    """Dynamic components that can rerun"""
    # Initialize session state
    if 'initial_load' not in st.session_state:
        st.session_state.initial_load = True
        st.session_state.filtered_df = pd.DataFrame()
        st.session_state.search_query = ""

    # Search input
    new_query = st.text_input("Pesquisar por Unidades Produtivas:", "").strip().lower()
    
    # Only update when search changes
    if new_query != st.session_state.search_query:
        st.session_state.search_query = new_query
        if st.session_state.search_query:
            st.session_state.filtered_df = st.session_state.df[
                st.session_state.df["Nome"].str.lower().str.contains(
                    st.session_state.search_query, 
                    regex=False
                )
            ]
        else:
            st.session_state.filtered_df = st.session_state.df

    # Display search results
    if st.session_state.search_query and st.session_state.filtered_df.empty:
        st.warning("Nenhuma unidade encontrada com esse nome")

    # Create map with current filtered data
    if not st.session_state.df.empty:
        m = create_base_map(st.session_state.geojson_data)
        legend = create_legend(st.session_state.geojson_data)
        m.get_root().html.add_child(legend)
        
        # Add dynamic markers
        for _, row in st.session_state.filtered_df.iterrows():
            icon_url = ICON_URLS.get(row["Numeral"], DEFAULT_ICON)
            icon = folium.CustomIcon(icon_url, icon_size=(32, 32), icon_anchor=(16, 16))
            
            Marker(
                location=[row["lat"], row["lon"]],
                popup=POPUP_TEMPLATE.format(row['Nome'], row['Tipo'], row['Regional']),
                icon=icon,
                tooltip=TOOLTIP_TEMPLATE.format(row['Nome'])
            ).add_to(m)
        
        st_folium(m, width=1400, height=700)

# --- Static Layout ---
def static_layout():
    """Components that never need to rerun"""
    st.logo(LOGO_PMC, size="large", link="https://portal.contagem.mg.gov.br/")
    st.title(APP_TITLE)
    st.header(APP_SUB_TITLE)
    
    # Load data once
    if 'df' not in st.session_state:
        st.session_state.df = load_data()
        st.session_state.geojson_data = load_geojson()
    
    # Display banners
    for url in BANNER_URLS:
        st.image(url, use_container_width=True)
    
    st.caption(APP_CAPTION)

# --- Execution Flow ---
if __name__ == "__main__":
    static_layout()    # Runs once
    main_app()         # Runs on search changes
