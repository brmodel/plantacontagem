# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl
import numpy as np
import json
import base64

# --- Configurações ---
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
APP_DESC = "Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF), em parceria com a Prefeitura Municipal de Contagem - MG"
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"

ICON_DEFINITIONS = {
    1: {"file": "leaf_green.png", "label": "Comunitária"},
    2: {"file": "leaf_blue.png", "label": "Institucional"},
    3: {"file": "leaf_orange.png", "label": "Comunitária/Institucional"},
    4: {"file": "leaf_purple.png", "label": "Feira da Cidade"},
}
ICONE_PADRAO_FILENAME = "leaf_green.png"

MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
    5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
}
BANNER_PMC_BASE_FILENAMES = ["ilustracao_pmc.png", "banner_pmc.png"]
LOGO_PMC_FILENAME = "contagem_sem_fome.png"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"
MAX_SIDEBAR_INFO_CHARS = 250

# Configurações do Mapa Interativo
CENTRO_INICIAL_MAPA = [-19.8888, -44.0535] # Coordenadas de Contagem
ZOOM_INICIAL_MAPA = 12
ZOOM_SELECIONADO_MAPA = 16 # Nível de zoom ao clicar em um marcador


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
LOGO_PMC_URL = ICONES_URL_BASE + LOGO_PMC_FILENAME
BANNER_PMC_URLS = [ICONES_URL_BASE + fname for fname in BANNER_PMC_BASE_FILENAMES]

# --- Templates HTML ---
POPUP_TEMPLATE_BASE = """
<div style="font-family: Arial, sans-serif; font-size: 12px; width: auto; max-width: min(90vw, 466px); min-width: 200px; word-break: break-word; box-sizing: border-box; padding: 8px;">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{}</b></h6>
    <p style="margin: 4px 0;"><b>Tipo:</b> {}</p>
    <p style="margin: 4px 0;"><b>Regional:</b> {}</p>
    {} </div>"""
TOOLTIP_TEMPLATE = """<div style="font-family: Arial, sans-serif; font-size: 14px"><p><b>Unidade Produtiva:</b><br>{}</p></div>"""

# --- Funções de Carregamento de Dados ---
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
    try:
        data = pd.read_csv(url, usecols=range(8))
        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True)
        data['Numeral'] = data['Numeral'].astype('Int64')
        for col in ['Nome', 'Tipo', 'Regional', 'Info', 'Instagram']:
            if col in data.columns:
                data[col] = data[col].astype(str).replace('nan', '', regex=False).replace('<NA>', '', regex=False)
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
    default_geojson = {"type": "FeatureCollection", "features": []}
    try:
        response = requests.get(GEOJSON_URL, timeout=20)
        response.raise_for_status(); geojson_data = response.json()
        if not isinstance(geojson_data, dict) or "features" not in geojson_data:
            st.warning("Estrutura do GeoJSON inválida."); return default_geojson
        return geojson_data
    except requests.exceptions.Timeout: st.error(f"Timeout ao carregar GeoJSON: {GEOJSON_URL}"); return default_geojson
    except requests.exceptions.RequestException as e: st.error(f"Erro de rede ao carregar GeoJSON: {e}"); return default_geojson
    except ValueError as e: st.error(f"Erro ao decodificar GeoJSON: {e}"); return default_geojson
    except Exception as e: st.error(f"Erro inesperado ao carregar GeoJSON: {e}"); return default_geojson

# --- Funções de Criação do Mapa e Legenda ---
def criar_legenda(geojson_data):
    regions = []
    if geojson_data and isinstance(geojson_data, dict) and 'features' in geojson_data:
        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {}); regions.append({'id': props.get('id'), 'name': props.get('Name')})
    items_legenda_regional = []
    for region in sorted(regions, key=lambda x: x.get('id', float('inf'))):
        color = MAPEAMENTO_CORES.get(region.get('id'), "#CCCCCC"); region_name = region.get('name', 'N/A')
        if region_name and region_name != 'N/A' and color:
            items_legenda_regional.append(f"""<div style="display: flex; align-items: center; margin: 2px 0;"><div style="background: {color}; width: 20px; height: 20px; margin-right: 5px; border: 1px solid #ccc;"></div><span>{region_name}</span></div>""")
    html_regional = f"""<div style="font-weight: bold; margin-bottom: 5px;">Regionais</div>{"".join(items_legenda_regional)}""" if items_legenda_regional else ""
    items_legenda_icones = []
    for key, props in sorted(ICON_DEFINITIONS.items()):
        icon_full_url = ICONES_URL_BASE + props["file"]
        icon_src_for_html = get_image_as_base64(icon_full_url) or icon_full_url
        legenda_texto = props["label"]
        items_legenda_icones.append(f"""<div style="display: flex; align-items: center; margin: 2px 0;"><img src="{icon_src_for_html}" alt="{legenda_texto}" title="{legenda_texto}" style="width: 20px; height: 20px; margin-right: 5px; object-fit: contain;"><span>{legenda_texto}</span></div>""")
    html_icones = f"""<div style="font-weight: bold; margin-top: 10px; margin-bottom: 5px;">Tipos de Unidade</div>{"".join(items_legenda_icones)}""" if items_legenda_icones else ""
    if html_regional or html_icones:
        return folium.Element(f"""<div style="position: fixed; bottom: 50px; right: 20px; z-index: 1000; background: rgba(255, 255, 255, 0.9); padding: 10px; border-radius: 5px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-family: Arial, sans-serif; font-size: 12px; max-width: 180px; max-height: 350px; overflow-y: auto;">{html_regional}{html_icones}</div>""")
    return None

def criar_mapa(data, geojson_data):
    # O location e zoom_start aqui definem o estado inicial do objeto Folium,
    # mas st_folium pode substituí-los com seus próprios parâmetros center/zoom.
    m = folium.Map(location=CENTRO_INICIAL_MAPA, tiles="cartodbpositron", zoom_start=ZOOM_INICIAL_MAPA, control_scale=True)
    if geojson_data and isinstance(geojson_data, dict) and geojson_data.get("features"):
        folium.GeoJson( geojson_data, name='Regionais',
            style_function=lambda x: {"fillColor": MAPEAMENTO_CORES.get(x['properties'].get('id'), "#CCCCCC"), "color": "#555555", "weight": 1, "fillOpacity": 0.35},
            tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
            highlight_function=lambda x: {"weight": 2.5, "fillOpacity": 0.6, "color": "black"},
            interactive=True, control=True, show=True).add_to(m)
    legenda_element = criar_legenda(geojson_data)
    if legenda_element: m.get_root().html.add_child(legenda_element)

    if isinstance(data, pd.DataFrame) and not data.empty:
        coord_precision = 6
        try:
            valid_coords = data[['lat', 'lon']].apply(pd.to_numeric, errors='coerce').dropna()
            rounded_coords = list(zip(np.round(valid_coords['lat'], coord_precision), np.round(valid_coords['lon'], coord_precision)))
            valid_data_dict = data.loc[valid_coords.index].to_dict('records')
            st.session_state.marker_lookup = dict(zip(rounded_coords, valid_data_dict))
        except Exception as e:
            st.warning(f"Erro ao criar lookup de marcadores: {e}.");
            if 'marker_lookup' not in st.session_state: st.session_state.marker_lookup = {}
        feature_groups = {num: folium.FeatureGroup(name=props["label"], show=True) for num, props in ICON_DEFINITIONS.items()}
        default_feature_group = folium.FeatureGroup(name='Outras Categorias', show=True); default_group_needed = False
        icon_base64_cache = {key: get_image_as_base64(ICONES_URL_BASE + props["file"]) for key, props in ICON_DEFINITIONS.items()}
        default_icon_base64 = get_image_as_base64(ICONE_PADRAO_URL)
        for index, row in data.iterrows():
            if pd.isna(row["lat"]) or pd.isna(row["lon"]): continue
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
            marker = Marker(location=[lat,lon], popup=popup, icon=current_icon, tooltip=TOOLTIP_TEMPLATE.format(row.get('Nome','N/I')))
            if icon_num in feature_groups: marker.add_to(feature_groups[icon_num])
            else: marker.add_to(default_feature_group); default_group_needed = True
        for group in feature_groups.values(): group.add_to(m)
        if default_group_needed: default_feature_group.add_to(m)
    LocateControl(strings={"title":"Mostrar minha localização", "popup":"Você está aqui"}).add_to(m)
    folium.LayerControl(position='topright').add_to(m)
    return m

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="expanded")

    if 'selected_marker_info' not in st.session_state: st.session_state.selected_marker_info = None
    if 'search_input_value' not in st.session_state: st.session_state.search_input_value = ''
    if 'marker_lookup' not in st.session_state: st.session_state.marker_lookup = {}
    # Inicializa o estado do centro e zoom do mapa
    if 'map_center' not in st.session_state: st.session_state.map_center = CENTRO_INICIAL_MAPA
    if 'map_zoom' not in st.session_state: st.session_state.map_zoom = ZOOM_INICIAL_MAPA
    
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False; st.session_state.load_error = False
        st.session_state.df = pd.DataFrame(); st.session_state.geojson_data = None
    if not st.session_state.data_loaded:
        with st.spinner("Carregando dados..."):
            loaded_df = load_data()
            if not loaded_df.empty: st.session_state.df = loaded_df
            else: st.session_state.load_error = True
            st.session_state.geojson_data = load_geojson() # Carrega GeoJSON também
        st.session_state.data_loaded = True
        
    col1, col2 = st.columns([3, 1])
    with col1: st.title(APP_TITULO); st.header(APP_SUBTITULO)
    with col2:
        logo_bytes = get_image_bytes(LOGO_PMC_URL)
        if logo_bytes: st.image(logo_bytes, width=150)
        else: st.image(LOGO_PMC_URL, width=150)
        def clear_selection_on_search():
            st.session_state.selected_marker_info = None
            st.session_state.search_input_value = st.session_state.search_input_widget_key
            # Opcional: Resetar zoom ao pesquisar?
            # st.session_state.map_center = CENTRO_INICIAL_MAPA
            # st.session_state.map_zoom = ZOOM_INICIAL_MAPA
        search_query = st.text_input("Pesquisar por Nome:", key="search_input_widget_key",
                                     on_change=clear_selection_on_search, value=st.session_state.search_input_value).strip().lower()
    with st.sidebar:
        st.title("Detalhes da Unidade")
        selected_info = st.session_state.selected_marker_info
        if selected_info:
            st.header(selected_info.get('Nome', 'N/I'))
            st.write(f"**Tipo:** {selected_info.get('Tipo', 'N/I')}")
            st.write(f"**Regional:** {selected_info.get('Regional', 'N/I')}")
            redes = selected_info.get('Instagram', '').strip()
            if redes:
                link_ig = redes if redes.startswith(('http://','https://')) else 'https://'+redes
                st.write(f"**Instagram:**"); st.markdown(f"[{redes}]({link_ig})")
            info_text_sidebar = selected_info.get('Info', '').strip()
            if info_text_sidebar:
                st.write(f"**Informações:**")
                if len(info_text_sidebar) > MAX_SIDEBAR_INFO_CHARS:
                    truncated_info = info_text_sidebar[:MAX_SIDEBAR_INFO_CHARS]+"..."
                    st.markdown(truncated_info)
                    with st.expander("Ler mais"): st.markdown(info_text_sidebar)
                else: st.markdown(info_text_sidebar)
        else: st.info("Clique em um marcador no mapa para ver os detalhes aqui.")

    df_filtrado = pd.DataFrame()
    if not st.session_state.load_error and not st.session_state.df.empty:
        df_original = st.session_state.df
        if search_query and 'Nome' in df_original.columns:
            try:
                df_filtrado = df_original[df_original["Nome"].str.contains(search_query,case=False,na=False,regex=False)]
                if df_filtrado.empty and search_query: st.warning(f"Nenhuma unidade encontrada com '{search_query}'.")
            except Exception as e: st.error(f"Erro no filtro: {e}"); df_filtrado = df_original
        elif search_query: st.warning("Coluna 'Nome' não encontrada."); df_filtrado = pd.DataFrame()
        else: df_filtrado = df_original
    
    if not df_filtrado.empty:
        # Cria o objeto mapa. Ele é leve pois os dados pesados são cacheados.
        m = criar_mapa(df_filtrado, st.session_state.get('geojson_data'))
        
        # Renderiza o mapa com o centro e zoom controlados pelo session_state
        map_output = st_folium(
            m,
            center=st.session_state.map_center, # Passa o centro do mapa dinamicamente
            zoom=st.session_state.map_zoom,     # Passa o zoom do mapa dinamicamente
            width='100%', height=600, key="folium_map_interactive", # Chave pode ser ajustada se necessário
            returned_objects=['last_object_clicked']
        )
        
        # Lógica de interação com o clique no mapa
        if map_output and map_output.get('last_object_clicked'):
            clicked_obj = map_output['last_object_clicked']
            # Se clicou em um marcador (tem lat/lng)
            if clicked_obj and 'lat' in clicked_obj and 'lng' in clicked_obj:
                clicked_lat = clicked_obj['lat']; clicked_lon = clicked_obj['lng']
                rounded_clicked_key = (round(clicked_lat, 6), round(clicked_lon, 6))
                found_info = st.session_state.get('marker_lookup', {}).get(rounded_clicked_key)

                if found_info is not None:
                    # Se o marcador encontrado é diferente do já selecionado OU se nenhum estava selecionado
                    if found_info != st.session_state.selected_marker_info:
                        st.session_state.selected_marker_info = found_info
                        st.session_state.map_center = [found_info['lat'], found_info['lon']] # Centraliza no marcador
                        st.session_state.map_zoom = ZOOM_SELECIONADO_MAPA                  # Aplica zoom
                        st.rerun()
                # Se clicou em um marcador mas não achou info (improvável com lookup correto)
                elif st.session_state.selected_marker_info is not None: 
                    st.session_state.selected_marker_info = None
                    st.session_state.map_center = CENTRO_INICIAL_MAPA # Reseta centro
                    st.session_state.map_zoom = ZOOM_INICIAL_MAPA     # Reseta zoom
                    st.rerun()
            # Se clicou fora de um marcador (ou em um GeoJSON, etc.)
            elif st.session_state.selected_marker_info is not None: # Apenas se algo estava selecionado
                st.session_state.selected_marker_info = None
                st.session_state.map_center = CENTRO_INICIAL_MAPA # Reseta centro
                st.session_state.map_zoom = ZOOM_INICIAL_MAPA     # Reseta zoom
                st.rerun()
                
    elif st.session_state.load_error: st.error("Falha crítica ao carregar dados. Mapa não pode ser exibido.")
    elif not st.session_state.df.empty and df_filtrado.empty and search_query: pass
    elif not st.session_state.data_loaded: st.info("Carregando dados iniciais...")
    else:
        if st.session_state.df.empty and not st.session_state.load_error:
            st.info("Não há dados de unidades produtivas disponíveis para carregar ou exibir.")

    st.markdown("---"); st.caption(APP_DESC)
    if len(BANNER_PMC_URLS) > 1:
        cols_banner = st.columns(len(BANNER_PMC_URLS))
        for i, url in enumerate(BANNER_PMC_URLS):
            with cols_banner[i]:
                banner_bytes = get_image_bytes(url)
                if banner_bytes: st.image(banner_bytes, use_container_width=True)
                else: st.image(url, use_container_width=True)
    elif BANNER_PMC_URLS:
        banner_bytes = get_image_bytes(BANNER_PMC_URLS[0])
        if banner_bytes: st.image(banner_bytes, use_container_width=True)
        else: st.image(BANNER_PMC_URLS[0], use_container_width=True)

if __name__ == "__main__":
    main()
