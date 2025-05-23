# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl
import numpy as np
import json # Not strictly used in this version, but often useful
import base64

# --- Configurações ---
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
APP_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF) "
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
PMC_PORTAL_URL = "https://portal.contagem.mg.gov.br"

ICON_DEFINITIONS = {
    1: {"file": "leaf_green.png", "label": "Comunitária"},
    2: {"file": "leaf_blue.png", "label": "Institucional"},
    3: {"file": "leaf_orange.png", "label": "Comunitária/Institucional"},
    4: {"file": "feira_cidade.png", "label": "Feira da Cidade"},
    5: {"file": "banco_alimentos.png", "label": "Banco de Alimentos"},
    6: {"file": "restaurante_pop.png", "label": "Restaurante Popular"},
    9: {"file": "sede_cmauf.png", "label": "Sede CMAUF"}
}
ICONE_PADRAO_FILENAME = "leaf_green.png"

MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
    5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
}

BANNER_PMC_BASE_FILENAMES_RODAPE = ["governo_federal.png", "alimenta_cidades.png", "contagem_sem_fome.png"]
LOGO_PMC_FILENAME = "banner_pmc.png"
FOOTER_BANNER_FILENAMES = BANNER_PMC_BASE_FILENAMES_RODAPE + [LOGO_PMC_FILENAME]
FIRST_TWO_FOOTER_BANNERS = ["governo_federal.png", "alimenta_cidades.png"]


GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"
MAX_POPOVER_INFO_CHARS = 250 # Max characters for info in popover before expander

CENTRO_INICIAL_MAPA = [-19.8888, -44.0535]
ZOOM_INICIAL_MAPA = 12
ZOOM_SELECIONADO_MAPA = 16


# --- Funções de Cache de Imagem ---
@st.cache_data(show_spinner=False)
def get_image_as_base64(image_url: str) -> str | None:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        img_bytes = response.content
        content_type = response.headers.get('Content-Type', 'image/png')
        return f"data:{content_type};base64,{base64.b64encode(img_bytes).decode()}"
    except requests.exceptions.RequestException as e:
        print(f"Erro ao carregar imagem {image_url} como Base64: {e}")
        return None

@st.cache_data(show_spinner=False)
def get_image_bytes(image_url: str) -> bytes | None:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Erro ao carregar bytes da imagem {image_url}: {e}")
        return None

# --- URLs e Rótulos Pré-calculados ---
ICONE_LEGENDA = {key: props["label"] for key, props in ICON_DEFINITIONS.items()}
ICONE_PADRAO_URL = ICONES_URL_BASE + ICONE_PADRAO_FILENAME
LOGO_PMC_URL_CABEÇALHO = ICONES_URL_BASE + LOGO_PMC_FILENAME
BANNER_PMC_URLS_RODAPE = [ICONES_URL_BASE + fname for fname in FOOTER_BANNER_FILENAMES]

# --- Templates HTML ---
POPUP_TEMPLATE_BASE = """
<div style="font-family: Arial, sans-serif; font-size: 12px; width: auto; max-width: min(90vw, 466px); min-width: 200px; word-break: break-word; box-sizing: border-box; padding: 8px;">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{}</b></h6>
    <p style="margin: 4px 0;"><b>Tipo:</b> {}</p>
    <p style="margin: 4px 0;"><b>Regional:</b> {}</p>
    {} </div>"""
TOOLTIP_TEMPLATE = """<div style="font-family: Arial, sans-serif; font-size: 14px"><p><b>{}:</b><br>{}</p></div>"""

# --- Funções de Carregamento de Dados ---
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
    try:
        data = pd.read_csv(url, usecols=range(8)) # Assuming first 8 columns are relevant
        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True) # Ensure essential fields are present
        data['Numeral'] = data['Numeral'].astype('Int64') # Use Int64 to handle potential NaNs if any slip through
        for col in ['Nome', 'Tipo', 'Regional', 'Info', 'Instagram']:
            if col in data.columns:
                data[col] = data[col].astype(str).replace('nan', '', regex=False).replace('<NA>', '', regex=False)
        # Validate 'Numeral' values (optional, for debugging)
        expected_numerals = set(ICON_DEFINITIONS.keys())
        for num_val in data['Numeral'].unique():
            if num_val not in expected_numerals:
                st.warning(f"Valor de 'Numeral' ({num_val}) não mapeado. Será usado o ícone padrão.")
        return data
    except pd.errors.EmptyDataError: st.error("Erro: A planilha parece estar vazia ou sem cabeçalhos."); return pd.DataFrame()
    except ValueError as e: st.error(f"Erro ao processar colunas: {e}."); return pd.DataFrame()
    except Exception as e: st.error(f"Erro inesperado ao carregar dados: {e}"); return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    default_geojson = {"type": "FeatureCollection", "features": []} # Default empty GeoJSON
    try:
        response = requests.get(GEOJSON_URL, timeout=20)
        response.raise_for_status(); geojson_data = response.json()
        # Basic validation of GeoJSON structure
        if not isinstance(geojson_data, dict) or "features" not in geojson_data:
            st.warning("Estrutura do GeoJSON inválida."); return default_geojson
        return geojson_data
    except requests.exceptions.Timeout: st.error(f"Timeout ao carregar GeoJSON: {GEOJSON_URL}"); return default_geojson
    except requests.exceptions.RequestException as e: st.error(f"Erro de rede ao carregar GeoJSON: {e}"); return default_geojson
    except ValueError as e: # Handles JSON decoding errors
        st.error(f"Erro ao decodificar GeoJSON: {e}"); return default_geojson
    except Exception as e: st.error(f"Erro inesperado ao carregar GeoJSON: {e}"); return default_geojson


# --- Funções de Criação do Mapa e Legenda ---
def criar_legenda(geojson_data):
    regions = []
    if geojson_data and isinstance(geojson_data, dict) and 'features' in geojson_data:
        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {}); regions.append({'id': props.get('id'), 'name': props.get('Name')})
    items_legenda_regional = []
    for region in sorted(regions, key=lambda x: x.get('id', float('inf'))): # Sort by ID
        color = MAPEAMENTO_CORES.get(region.get('id'), "#CCCCCC"); region_name = region.get('name', 'N/A')
        if region_name and region_name != 'N/A' and color: # Ensure valid data
            items_legenda_regional.append(f"""<div style="display: flex; align-items: center; margin: 2px 0;"><div style="background: {color}; width: 20px; height: 20px; margin-right: 5px; border: 1px solid #ccc;"></div><span>{region_name}</span></div>""")
    html_regional = f"""<div style="font-weight: bold; margin-bottom: 5px;">Regionais</div>{"".join(items_legenda_regional)}""" if items_legenda_regional else ""
    items_legenda_icones = []
    for key, props in sorted(ICON_DEFINITIONS.items()): # Sort by key for consistent order
        icon_full_url = ICONES_URL_BASE + props["file"]
        icon_src_for_html = get_image_as_base64(icon_full_url) or icon_full_url # Fallback to URL if base64 fails
        legenda_texto = props["label"]
        items_legenda_icones.append(f"""<div style="display: flex; align-items: center; margin: 2px 0;"><img src="{icon_src_for_html}" alt="{legenda_texto}" title="{legenda_texto}" style="width: 20px; height: 20px; margin-right: 5px; object-fit: contain;"><span>{legenda_texto}</span></div>""")
    html_icones = f"""<div style="font-weight: bold; margin-top: 10px; margin-bottom: 5px;">Tipos de Unidade</div>{"".join(items_legenda_icones)}""" if items_legenda_icones else ""
    if html_regional or html_icones:
        return folium.Element(f"""<div style="position: fixed; bottom: 50px; right: 20px; z-index: 1000; background: rgba(255, 255, 255, 0.9); padding: 10px; border-radius: 5px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-family: Arial, sans-serif; font-size: 12px; max-width: 180px; max-height: 450px; overflow-y: auto;">{html_regional}{html_icones}</div>""")
    return None

def criar_mapa(data, geojson_data):
    m = folium.Map(location=CENTRO_INICIAL_MAPA, tiles="cartodbpositron", zoom_start=ZOOM_INICIAL_MAPA, control_scale=True)
    if geojson_data and isinstance(geojson_data, dict) and geojson_data.get("features"):
        folium.GeoJson( geojson_data, name='Regionais',
            style_function=lambda x: {"fillColor": MAPEAMENTO_CORES.get(x['properties'].get('id'), "#CCCCCC"), "color": "#555555", "weight": 1, "fillOpacity": 0.35},
            tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
            highlight_function=lambda x: {"weight": 2.5, "fillOpacity": 0.6, "color": "black"}, # Highlight style
            interactive=True, control=True, show=True).add_to(m)
    legenda_element = criar_legenda(geojson_data)
    if legenda_element: m.get_root().html.add_child(legenda_element)

    if isinstance(data, pd.DataFrame) and not data.empty:
        coord_precision = 6 # Precision for lat/lon key in marker_lookup
        try:
            # Ensure lat/lon are numeric before rounding, drop if not
            valid_coords = data[['lat', 'lon']].apply(pd.to_numeric, errors='coerce').dropna()
            # Create rounded coordinate tuples for lookup
            rounded_coords = list(zip(np.round(valid_coords['lat'], coord_precision), np.round(valid_coords['lon'], coord_precision)))
            # Create dictionary of marker data, indexed by original DataFrame index of valid_coords
            valid_data_dict = data.loc[valid_coords.index].to_dict('records')
            st.session_state.marker_lookup = dict(zip(rounded_coords, valid_data_dict))
        except Exception as e:
            st.warning(f"Erro ao criar lookup de marcadores: {e}.");
            if 'marker_lookup' not in st.session_state: st.session_state.marker_lookup = {} # Ensure it exists

        feature_groups = {num: folium.FeatureGroup(name=props["label"], show=True) for num, props in ICON_DEFINITIONS.items()}
        default_feature_group = folium.FeatureGroup(name='Outras Categorias', show=True); default_group_needed = False
        icon_base64_cache = {key: get_image_as_base64(ICONES_URL_BASE + props["file"]) for key, props in ICON_DEFINITIONS.items()}
        default_icon_base64 = get_image_as_base64(ICONE_PADRAO_URL)

        for index, row in data.iterrows():
            if pd.isna(row["lat"]) or pd.isna(row["lon"]): continue # Skip if no coordinates
            lat, lon = row["lat"], row["lon"]
            icon_num = int(row["Numeral"]) if pd.notna(row["Numeral"]) else None
            icon_b64_data = icon_base64_cache.get(icon_num, default_icon_base64)
            current_icon = folium.CustomIcon(icon_b64_data, icon_size=(25,25), icon_anchor=(0,20), popup_anchor=(0,-10)) if icon_b64_data else folium.Icon(color="green", prefix='fa', icon="leaf")
            
            popup_parts = []
            instagram_link = row.get('Instagram', '').strip()
            if instagram_link:
                link_ig_safe = instagram_link if instagram_link.startswith(('http://','https://')) else 'https://'+instagram_link
                popup_parts.append(f"<p style='margin:4px 0;'><b>Instagram:</b> <a href='{link_ig_safe}' target='_blank' rel='noopener noreferrer'>{instagram_link}</a></p>")
            
            popup_content = POPUP_TEMPLATE_BASE.format(row.get('Nome','N/I'), row.get('Tipo','N/I'), row.get('Regional','N/I'), "".join(popup_parts))
            popup = folium.Popup(popup_content, max_width=450)
            marker = Marker(location=[lat,lon], popup=popup, icon=current_icon, tooltip=TOOLTIP_TEMPLATE.format(row.get('Tipo','N/I'), row.get('Nome','N/I')))
            
            if icon_num in feature_groups: marker.add_to(feature_groups[icon_num])
            else: marker.add_to(default_feature_group); default_group_needed = True
        
        for group in feature_groups.values(): group.add_to(m)
        if default_group_needed: default_feature_group.add_to(m)
        
    LocateControl(strings={"title":"Mostrar minha localização", "popup":"Você está aqui"}).add_to(m)
    folium.LayerControl(position='bottomleft').add_to(m)
    return m

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="collapsed") # Sidebar collapsed by default

    # Injeção de CSS
    st.markdown(
        """
        <style>
        /* General App Header Style */
        .stApp > header {
            position: relative; /* Ensure header stays in flow, helps with z-index if needed */
            z-index: 1000; /* Keep header above other elements if overlap occurs */
        }

        /* Hide default Streamlit page navigation in sidebar (if pages/ dir exists) */
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Align content within Streamlit columns to the top by default */
        div[data-testid="stColumns"] > div[data-testid^="stVerticalBlock"] { /* More specific selector for column children */
            display: flex;
            flex-direction: column;
            justify-content: flex-start; 
        }
        
        /* Remove default margins from h3 elements within columns for tighter layout */
        div[data-testid^="stVerticalBlock"] h3 { /* Target h3 within column blocks */
            margin-top: 0px !important; 
            margin-bottom: 0px !important; 
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }

        /* Style for the search bar column container */
        div[data-testid="column-search-bar"] {
            display: flex;
            align-items: center; /* Vertically center content */
            justify-content: center; /* Horizontally center content */
            height: 100%; 
        }
        
        /* Style for the PMC logo column container */
        div[data-testid="column-PMC-logo"] {
            display: flex;
            align-items: center; /* Vertically center content */
            justify-content: center; /* Horizontally center content */
            height: 100%;
            padding-top: 5px; /* Small padding to visually align with search bar if needed */
        }

        /* Style for the PMC logo image itself */
        div[data-testid="column-PMC-logo"] img {
            max-width: 100%; 
            height: auto;    
            max-height: 60px; /* Constrain logo height to help with alignment */
            object-fit: contain; 
        }
        
        /* Ensure search input doesn't have extra top/bottom margins */
        div[data-testid="column-search-bar"] .stTextInput {
            margin-top: 0px; 
            margin-bottom: 0px; 
        }

        /* Popover styling */
        div[data-testid="stPopover"] div[data-testid="stVerticalBlock"] {
             padding: 10px; /* Add some padding inside the popover */
        }
        </style>
        """, unsafe_allow_html=True
    )

    # Initialize session state variables
    if 'selected_marker_info' not in st.session_state: st.session_state.selected_marker_info = None
    if 'search_input_value' not in st.session_state: st.session_state.search_input_value = ''
    if 'marker_lookup' not in st.session_state: st.session_state.marker_lookup = {}
    if 'map_center' not in st.session_state: st.session_state.map_center = CENTRO_INICIAL_MAPA
    if 'map_zoom' not in st.session_state: st.session_state.map_zoom = ZOOM_INICIAL_MAPA
    
    # Load data if not already loaded
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False; st.session_state.load_error = False
        st.session_state.df = pd.DataFrame(); st.session_state.geojson_data = None
    if not st.session_state.data_loaded:
        with st.spinner("Carregando dados..."):
            loaded_df = load_data()
            if not loaded_df.empty: st.session_state.df = loaded_df
            else: st.session_state.load_error = True
            st.session_state.geojson_data = load_geojson()
        st.session_state.data_loaded = True
        
    # --- Header Layout ---
    st.title(APP_TITULO)
    
    # Main header columns
    header_col1, header_col2, header_col3 = st.columns([0.6, 0.25, 0.15]) # Adjusted ratios for better balance

    with header_col1:
        st.header(APP_SUBTITULO)
        if st.button("Saiba Mais sobre o Projeto"):
            st.switch_page("pages/saiba_mais.py")
            
    with header_col2:
        st.markdown('<div data-testid="column-search-bar">', unsafe_allow_html=True)
        def clear_selection_on_search(): # Callback to clear selection if search changes
            st.session_state.selected_marker_info = None
            st.session_state.show_popover = False


        search_query = st.text_input(
            "Pesquisar por Nome, Tipo ou Regional:",
            key="search_input_widget_key", # Unique key for the widget
            on_change=clear_selection_on_search,
            value=st.session_state.search_input_value,
            label_visibility="collapsed" # Hide label, use placeholder
        ).strip().lower()
        st.session_state.search_input_value = search_query
        st.markdown('</div>', unsafe_allow_html=True)

    with header_col3:
        st.markdown('<div data-testid="column-PMC-logo">', unsafe_allow_html=True)
        logo_bytes = get_image_bytes(LOGO_PMC_URL_CABEÇALHO)
        if logo_bytes:
            st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="data:image/png;base64,{base64.b64encode(logo_bytes).decode()}"></a>', unsafe_allow_html=True)
        else: # Fallback if image bytes fail to load
            st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="{LOGO_PMC_URL_CABEÇALHO}"></a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Popover for Marker Details ---
    # The popover will be rendered here if selected_marker_info is set
    # We use a placeholder to anchor the popover
    popover_anchor = st.empty() 

    if st.session_state.get("selected_marker_info"):
        with popover_anchor.popover("Detalhes da Unidade", use_container_width=True):
            selected_info = st.session_state.selected_marker_info
            st.header(selected_info.get('Nome', 'N/I'))
            st.write(f"**Tipo:** {selected_info.get('Tipo', 'N/I')}")
            st.write(f"**Regional:** {selected_info.get('Regional', 'N/I')}")
            redes = selected_info.get('Instagram', '').strip()
            if redes:
                link_ig = redes if redes.startswith(('http://','https://')) else 'https://'+redes
                st.write(f"**Instagram:**"); st.markdown(f"[{redes}]({link_ig})", unsafe_allow_html=True)
            
            info_text_popover = selected_info.get('Info', '').strip()
            if info_text_popover:
                st.write(f"**Informações:**")
                if len(info_text_popover) > MAX_POPOVER_INFO_CHARS:
                    truncated_info = info_text_popover[:MAX_POPOVER_INFO_CHARS]+"..."
                    st.markdown(truncated_info)
                    with st.expander("Ler mais"): st.markdown(info_text_popover)
                else:
                    st.markdown(info_text_popover)
            if st.button("Fechar Detalhes", key="close_popover_btn"):
                st.session_state.selected_marker_info = None
                st.rerun()


    # --- Data Filtering ---
    df_filtrado = pd.DataFrame()
    if not st.session_state.load_error and not st.session_state.df.empty:
        df_original = st.session_state.df
        if search_query: # Apply filter only if search_query is not empty
            try:
                # Initialize boolean Series for filtering
                filtro_nome = pd.Series([False] * len(df_original), index=df_original.index)
                filtro_tipo = pd.Series([False] * len(df_original), index=df_original.index)
                filtro_regional = pd.Series([False] * len(df_original), index=df_original.index)

                if 'Nome' in df_original.columns:
                    filtro_nome = df_original["Nome"].astype(str).str.contains(search_query, case=False, na=False, regex=False)
                if 'Tipo' in df_original.columns:
                    filtro_tipo = df_original["Tipo"].astype(str).str.contains(search_query, case=False, na=False, regex=False)
                if 'Regional' in df_original.columns:
                    filtro_regional = df_original["Regional"].astype(str).str.contains(search_query, case=False, na=False, regex=False)
                
                df_filtrado = df_original[filtro_nome | filtro_tipo | filtro_regional]

                if df_filtrado.empty and search_query: # Only show warning if search was active
                    st.warning(f"Nenhuma unidade encontrada com '{search_query}' no Nome, Tipo ou Regional.")
            except Exception as e:
                st.error(f"Erro no filtro: {e}"); df_filtrado = df_original # Fallback to original on error
        else:
            df_filtrado = df_original # No search query, show all data
    
    # --- Map Display ---
    if not df_filtrado.empty:
        m = criar_mapa(df_filtrado, st.session_state.get('geojson_data'))
        map_output = st_folium(
            m,
            center=st.session_state.map_center,
            zoom=st.session_state.map_zoom,
            width='100%', height=600, key="folium_map_interactive", # Unique key for the map
            returned_objects=['last_object_clicked'] # We only need the last clicked object
        )
        
        # Handle map click events
        if map_output and map_output.get('last_object_clicked'):
            clicked_obj = map_output['last_object_clicked']
            # Check if the click was on a marker (will have lat/lng)
            if clicked_obj and 'lat' in clicked_obj and 'lng' in clicked_obj:
                clicked_lat = clicked_obj['lat']; clicked_lon = clicked_obj['lng']
                # Use a consistent precision for lookup key
                rounded_clicked_key = (round(clicked_lat, 6), round(clicked_lon, 6))
                found_info = st.session_state.get('marker_lookup', {}).get(rounded_clicked_key)

                if found_info is not None:
                    # If a different marker is clicked, update info and map center/zoom
                    if found_info != st.session_state.selected_marker_info:
                        st.session_state.selected_marker_info = found_info
                        st.session_state.map_center = [found_info['lat'], found_info['lon']]
                        st.session_state.map_zoom = ZOOM_SELECIONADO_MAPA
                        st.rerun() 
                # If click was not on a known marker (e.g., on the map base) and a popover was open, clear it.
                elif st.session_state.selected_marker_info is not None: 
                    st.session_state.selected_marker_info = None
                    # Optionally reset map view or keep it as is
                    # st.session_state.map_center = CENTRO_INICIAL_MAPA 
                    # st.session_state.map_zoom = ZOOM_INICIAL_MAPA
                    st.rerun()
            # If click was on something else (e.g. GeoJSON region) and a popover was open, clear it.
            elif st.session_state.selected_marker_info is not None:
                st.session_state.selected_marker_info = None
                st.rerun()
                
    elif st.session_state.load_error: st.error("Falha crítica ao carregar dados. Mapa não pode ser exibido.")
    elif not st.session_state.df.empty and df_filtrado.empty and search_query: pass # Warning already shown
    elif not st.session_state.data_loaded: st.info("Carregando dados iniciais...") # Should be handled by spinner
    else: # df is empty and no load error
        if st.session_state.df.empty and not st.session_state.load_error:
            st.info("Não há dados de unidades produtivas disponíveis para carregar ou exibir.")

    # --- Footer ---
    st.markdown("---"); st.caption(APP_DESC)

    BASE_BANNER_RODAPE_HEIGHT_PX = 70 # Base height for most banners
    LARGER_BANNER_HEIGHT_PX = int(BASE_BANNER_RODAPE_HEIGHT_PX * 1.5) # Increased height for first two

    def display_banner_html(url: str, height_px: int, filename: str) -> str:
        base64_image_data = get_image_as_base64(url)
        image_source = base64_image_data if base64_image_data else url
        
        # Custom style for larger banners to ensure they fill width more
        img_style = f"""
            height: 100%; 
            width: auto;  
            max-width: 100%; 
            object-fit: contain; 
            display: block;
        """
        if filename in FIRST_TWO_FOOTER_BANNERS:
             img_style = f"""
                height: auto; /* Allow height to adjust */
                width: 90%;  /* Try to fill more width */
                max-height: {height_px}px; /* But don't exceed the container height */
                object-fit: contain; 
                display: block;
                margin-left: auto; /* Center if it doesn't fill width */
                margin-right: auto;
            """


        return f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: {height_px}px;
            overflow: hidden;
            width: 100%;
            padding: 5px; /* Add some padding around banners */
        ">
            <img src="{image_source}" alt="Banner {filename}" style="{img_style}">
        </div>
        """

    if BANNER_PMC_URLS_RODAPE:
        num_banners = len(BANNER_PMC_URLS_RODAPE)
        # Use 4 columns for 4 banners, or fewer if less than 4.
        # Consider a more flexible column setup if number of banners can vary significantly.
        cols_banner = st.columns(num_banners if num_banners <= 4 else 4) 

        for i, url in enumerate(BANNER_PMC_URLS_RODAPE):
            filename = FOOTER_BANNER_FILENAMES[i]
            current_banner_height = LARGER_BANNER_HEIGHT_PX if filename in FIRST_TWO_FOOTER_BANNERS else BASE_BANNER_RODAPE_HEIGHT_PX
            
            # Distribute banners into columns
            # If more banners than columns, they will wrap if columns are full.
            # Here, we assume num_cols will accommodate all banners in one row.
            with cols_banner[i % len(cols_banner)]: 
                banner_html = display_banner_html(url, current_banner_height, filename)
                st.markdown(banner_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
