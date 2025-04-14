import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl

# --- Config ---
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

# Precomputed URLs
ICON_URLS = {k: ICON_BASE_URL + v for k, v in ICON_MAPPING.items()}
DEFAULT_ICON = ICON_BASE_URL + "leaf_green.png"
BANNER_URLS = [ICON_BASE_URL + img for img in IMAGE_BANNER_URLS]

# HTML Templates
TOOLTIP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px">
    <p><b>Unidade Produtiva:<br>{}</b></p>
</div>
"""

POPUP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px; min-width: 200px;">
    <h6 style="margin: 0 0 5px 0;"><b>{}</b></h6>
    <p style="margin: 2px 0;"><b>Tipo:</b> {}</p>
    <p style="margin: 2px 0;"><b>Regional:</b> {}</p>
</div>
"""

# --- Load Data ---
@st.cache_data(ttl=600)
def load_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
        data = pd.read_csv(url, usecols=range(6))
        clean_data = data.dropna(subset=['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral']).copy()
        clean_data['Numeral'] = clean_data['Numeral'].astype(int)
        return clean_data
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    try:
        response = requests.get(GEOJSON_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}

# --- Map Creation ---
def create_legend(geojson_data):
    """Create HTML legend for regional colors"""
    regions = []
    for feature in geojson_data.get('features', []):
        props = feature.get('properties', {})
        regions.append({
            'id': props.get('id'),
            'name': props.get('Name')
        })
    
    legend_items = []
    for region in sorted(regions, key=lambda x: x['id']):
        color = COLOR_MAPPING.get(region['id'], "#fddaec")
        legend_items.append(f"""
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="background: {color}; width: 20px; height: 20px; margin-right: 5px;"></div>
                <span>{region['name']}</span>
            </div>
        """)
    
    return folium.Element(f"""
        <div style="
            position: fixed; 
            bottom: 50px; 
            right: 20px; 
            z-index: 1000;
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            font-family: Arial;
            font-size: 12px;
            max-width: 150px;
        ">
            <div style="font-weight: bold; margin-bottom: 5px;">Regionais</div>
            {"".join(legend_items)}
        </div>
    """)

def create_map(data, geojson_data):
    m = folium.Map(location=[-19.89323, -43.97145], 
                 tiles="OpenStreetMap", 
                 zoom_start=12.49, 
                 control_scale=True)

    # Add non-interactive GeoJSON
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
        interactive=True,  # Disables all interaction including clicks
        control=True
    ).add_to(m)

    # Add markers
    for _, row in data.iterrows():
        icon_url = ICON_URLS.get(row["Numeral"], DEFAULT_ICON)
        icon = folium.CustomIcon(icon_url, icon_size=(42, 42), icon_anchor=(16, 16))
        
        Marker(
            location=[row["lat"], row["lon"]],
            popup=POPUP_TEMPLATE.format(row['Nome'], row['Tipo'], row['Regional']),
            icon=icon,
            tooltip=TOOLTIP_TEMPLATE.format(row['Nome'])
        ).add_to(m)

    # Add controls
    LocateControl().add_to(m)
    folium.LayerControl().add_to(m)
    
    # Add legend
    legend = create_legend(geojson_data)
    m.get_root().html.add_child(legend)

    return m

# --- Main App ---
def main():
    st.logo(LOGO_PMC, size="large", link="https://portal.contagem.mg.gov.br/")
    st.title(APP_TITLE)
    st.header(APP_SUB_TITLE)

    # Load data
    df = load_data()
    geojson_data = load_geojson()

    # Search functionality
    search_query = st.text_input("Pesquisar por Unidades Produtivas:", "").strip().lower()
    if search_query:
        filtered_df = df[df["Nome"].str.lower().str.contains(search_query, regex=False)]
        if filtered_df.empty:
            st.warning("Nenhuma unidade encontrada com esse nome")
    else:
        filtered_df = df

    # Display map
    if not df.empty:
        m = create_map(filtered_df, geojson_data)
        st_folium(m, width=1400, height=700)
    else:
        st.warning("Nenhum dado disponível para exibir")
    
    st.caption(APP_CAPTION)

    # Display banners
    for url in BANNER_URLS:
        st.image(url, use_container_width=True)

if __name__ == "__main__":
    main()
