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
APP_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF) "
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
PMC_PORTAL_URL = "https://portal.contagem.mg.gov.br" # URL do portal da PMC

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

# Nomes base dos arquivos para os banners do rodapé (excluindo o logo da PMC por enquanto)
BANNER_PMC_BASE_FILENAMES_RODAPE = ["governo_federal.png", "alimenta_cidades.png", "contagem_sem_fome.png"]
LOGO_PMC_FILENAME = "banner_pmc.png" # Arquivo do logo da PMC, também usado como banner no rodapé

# Lista combinada de nomes de arquivos para os banners do rodapé
FOOTER_BANNER_FILENAMES = BANNER_PMC_BASE_FILENAMES_RODAPE + [LOGO_PMC_FILENAME]

GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"
MAX_SIDEBAR_INFO_CHARS = 200

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

# URL para o logo da PMC no cabeçalho
LOGO_PMC_URL_CABEÇALHO = ICONES_URL_BASE + LOGO_PMC_FILENAME

# URLs para os banners do rodapé (agora incluindo o banner_pmc.png)
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
        return folium.Element(f"""<div style="position: fixed; bottom: 50px; right: 20px; z-index: 1000; background: rgba(255, 255, 255, 0.9); padding: 10px; border-radius: 5px; box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-family: Arial, sans-serif; font-size: 12px; max-width: 180px; max-height: 450px; overflow-y: auto;">{html_regional}{html_icones}</div>""")
    return None

def criar_mapa(data, geojson_data):
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
            marker = Marker(location=[lat,lon], popup=popup, icon=current_icon, tooltip=TOOLTIP_TEMPLATE.format(row.get('Tipo','N/I'), row.get('Nome','N/I')))
            if icon_num in feature_groups: marker.add_to(feature_groups[icon_num])
            else: marker.add_to(default_feature_group); default_group_needed = True
        for group in feature_groups.values(): group.add_to(m)
        if default_group_needed: default_feature_group.add_to(m)
    LocateControl(strings={"title":"Mostrar minha localização", "popup":"Você está aqui"}).add_to(m)
    folium.LayerControl(position='topright').add_to(m)
    return m

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="collapsed")

    # Injeção de CSS para alinhar verticalmente
    st.markdown(
        """
        <style>
        .stApp > header {
            position: relative;
            z-index: 1000;
        }

        /* Os contêineres das colunas do Streamlit são div com data-testid="stVerticalBlock" dentro de div com data-testid="stColumns" */
        /* Para alinhar o conteúdo interno das colunas ao topo */
        div[data-testid="stColumns"] > div > div {
            display: flex;
            flex-direction: column;
            justify-content: flex-start; /* Alinha os itens à parte de cima */
            height: 100%; /* Garante que a coluna ocupa a altura total */
        }
        
        /* Ajuste específico para o subtítulo para remover margens padrão indesejadas */
        div[data-testid="stVerticalBlock"] h3 {
            margin-top: 0px; 
            margin-bottom: 0px; 
            padding-top: 0px;
            padding-bottom: 0px;
        }

        /* Ajuste específico para a barra de busca na col2 (nova ordem) */
        div[data-testid="column-search-bar"] {
            display: flex;
            align-items: flex-start; /* Alinha o item ao topo */
            justify-content: center; /* Centraliza horizontalmente */
            height: 100%; /* Ocupa a altura total do flex container */
        }
        
        /* Ajuste específico para o logo da PMC na col3 (nova ordem) */
        div[data-testid="column-PMC-logo"] {
            display: flex;
            align-items: flex-start; /* Alinha o item ao topo */
            justify-content: center; /* Centraliza horizontalmente */
            height: 100%; /* Ocupa a altura total do flex container */
            margin-top: 42px; /* Desce o contêiner do logo em 40px */
        }

        /* Regra para a imagem do logo dentro do seu contêiner */
        div[data-testid="column-PMC-logo"] img {
            max-width: 100%; /* Garante que a imagem não exceda a largura da coluna */
            height: auto;    /* Mantém a proporção */
            object-fit: contain; /* Garante que a imagem se ajuste sem cortar */
        }

        /* Pequeno ajuste para o input da barra de busca para compensar o label */
        div[data-testid="column-search-bar"] .stTextInput {
            margin-top: 0px; /* Garante que não há margem superior extra */
            margin-bottom: 0px; /* Garante que não há margem inferior extra */
        }

        </style>
        """, unsafe_allow_html=True
    )

    if 'selected_marker_info' not in st.session_state: st.session_state.selected_marker_info = None
    if 'search_input_value' not in st.session_state: st.session_state.search_input_value = ''
    if 'marker_lookup' not in st.session_state: st.session_state.marker_lookup = {}
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
            st.session_state.geojson_data = load_geojson()
        st.session_state.data_loaded = True
        
    # APP_TITULO agora fora do container de colunas
    st.title(APP_TITULO)

    with st.container():
        # Definimos 3 colunas para o cabeçalho
        # Invertemos a ordem de col2 e col3 aqui para mudar a ordem visual
        col1, col2, col3 = st.columns([3, 1, 0.5]) # col2 agora tem o peso da busca, col3 o do logo
        
        with col1:
            st.header(APP_SUBTITULO) # Apenas o subtítulo aqui
            
        with col2: # Agora esta coluna é para a barra de busca
            # Adiciona um data-testid para o CSS customizado
            st.markdown('<div data-testid="column-search-bar">', unsafe_allow_html=True)
            def clear_selection_on_search():
                st.session_state.selected_marker_info = None

            search_query = st.text_input(
                "Pesquisar por Nome, Tipo ou Regional:",
                key="search_input_widget_key",
                on_change=clear_selection_on_search,
                value=st.session_state.search_input_value
            ).strip().lower()
            st.session_state.search_input_value = search_query
            st.markdown('</div>', unsafe_allow_html=True)

        with col3: # Agora esta coluna é para o logo da PMC
            # Adiciona um data-testid para o CSS customizado e aplica o margin-top
            st.markdown('<div data-testid="column-PMC-logo">', unsafe_allow_html=True)
            logo_bytes = get_image_bytes(LOGO_PMC_URL_CABEÇALHO)
            if logo_bytes:
                # Removemos o width="150" daqui
                st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="data:image/png;base64,{base64.b64encode(logo_bytes).decode()}"></a>', unsafe_allow_html=True)
            else:
                # Removemos o width="150" daqui
                st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="{LOGO_PMC_URL_CABEÇALHO}"></a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


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
        if search_query:
            try:
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

                if df_filtrado.empty and search_query:
                    st.warning(f"Nenhuma unidade encontrada com '{search_query}' no Nome, Tipo ou Regional.")
            except Exception as e:
                st.error(f"Erro no filtro: {e}");
                df_filtrado = df_original
        else:
            df_filtrado = df_original
    
    if not df_filtrado.empty:
        m = criar_mapa(df_filtrado, st.session_state.get('geojson_data'))
        map_output = st_folium(
            m,
            center=st.session_state.map_center,
            zoom=st.session_state.map_zoom,
            width='100%', height=600, key="folium_map_interactive",
            returned_objects=['last_object_clicked']
        )
        
        if map_output and map_output.get('last_object_clicked'):
            clicked_obj = map_output['last_object_clicked']
            if clicked_obj and 'lat' in clicked_obj and 'lng' in clicked_obj:
                clicked_lat = clicked_obj['lat']; clicked_lon = clicked_obj['lng']
                rounded_clicked_key = (round(clicked_lat, 6), round(clicked_lon, 6))
                found_info = st.session_state.get('marker_lookup', {}).get(rounded_clicked_key)

                if found_info is not None:
                    if found_info != st.session_state.selected_marker_info:
                        st.session_state.selected_marker_info = found_info
                        st.session_state.map_center = [found_info['lat'], found_info['lon']]
                        st.session_state.map_zoom = ZOOM_SELECIONADO_MAPA
                        st.rerun()
                elif st.session_state.selected_marker_info is not None: 
                    st.session_state.selected_marker_info = None
                    st.session_state.map_center = CENTRO_INICIAL_MAPA
                    st.session_state.map_zoom = ZOOM_INICIAL_MAPA
                    st.rerun()
            elif st.session_state.selected_marker_info is not None:
                st.session_state.selected_marker_info = None
                st.session_state.map_center = CENTRO_INICIAL_MAPA
                st.session_state.map_zoom = ZOOM_INICIAL_MAPA
                st.rerun()
                
    elif st.session_state.load_error: st.error("Falha crítica ao carregar dados. Mapa não pode ser exibido.")
    elif not st.session_state.df.empty and df_filtrado.empty and search_query: pass
    elif not st.session_state.data_loaded: st.info("Carregando dados iniciais...")
    else:
        if st.session_state.df.empty and not st.session_state.load_error:
            st.info("Não há dados de unidades produtivas disponíveis para carregar ou exibir.")

    st.markdown("---"); st.caption(APP_DESC)

    BANNER_RODAPE_HEIGHT_PX = 80

    def display_banner_html(url: str, height_px: int) -> str:
        base64_image_data = get_image_as_base64(url)
        image_source = base64_image_data if base64_image_data else url

        return f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: {height_px}px;
            overflow: hidden;
            width: 100%;
        ">
            <img src="{image_source}" alt="Banner" style="
                height: 100%; /* Prioriza a altura total do contêiner */
                width: auto;  /* Permite que a largura se ajuste automaticamente */
                max-width: 100%; /* Garante que a imagem não ultrapasse a largura da coluna */
                object-fit: contain; /* Mantém a proporção e se ajusta ao contêiner */
                display: block;
            ">
        </div>
        """

    if BANNER_PMC_URLS_RODAPE:
        num_banners = len(BANNER_PMC_URLS_RODAPE)
        num_cols = min(num_banners, 4)

        cols_banner = st.columns(num_cols)

        for i, url in enumerate(BANNER_PMC_URLS_RODAPE):
            with cols_banner[i % num_cols]:
                banner_html = display_banner_html(url, BANNER_RODAPE_HEIGHT_PX)
                st.markdown(banner_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
