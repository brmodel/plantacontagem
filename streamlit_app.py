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
import html

####### Configurações de ícones, base de dados, links de imagens e afins ######
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
APP_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF)"
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/icones/"
BANNER_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/"
PMC_PORTAL_URL = "https://portal.contagem.mg.gov.br"

ICONES_DEFINIDOS = {
    1: {"file": "leaf_green.png", "label": "Comunitária"},
    2: {"file": "leaf_blue.png", "label": "Institucional"},
    3: {"file": "leaf_orange.png", "label": "Comunitária/Institucional"},
    4: {"file": "feira_cidade.png", "label": "Feira da Cidade"},
    5: {"file": "banco_alimentos.png", "label": "Banco de Alimentos"},
    6: {"file": "restaurante_pop.png", "label": "Restaurante Popular"},
    9: {"file": "sede_cmauf.png", "label": "Sede CMAUF"}
}
ICONE_PADRAO_ARQUIVO = "leaf_green.png"

MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
    5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
}

LOGO_PMC_FILENAME = "banner_pmc.png"

LINK_GEOJSON = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"
LIMITE_CARACTERES = 250

CENTRO_INICIAL_MAPA = [-19.8888, -44.0535]
ZOOM_INICIAL_MAPA = 12
ZOOM_SELECIONADO_MAPA = 16

LINK_CONTAGEM_SEM_FOME = "https://portal.contagem.mg.gov.br/portal/noticias/0/3/67444/prefeitura-lanca-campanha-de-seguranca-alimentar-contagem-sem-fome"
LINK_ALIMENTA_CIDADES = "https://www.gov.br/mds/pt-br/acoes-e-programas/promocao-da-alimentacao-adequada-e-saudavel/alimenta-cidades"
LINK_GOVERNO_FEDERAL = "https://www.gov.br/pt-br"

RODAPE_PAGINA = [
    {
        "filename": "governo_federal.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/governo_federal.png",
        "link": LINK_GOVERNO_FEDERAL,
        "scale": 2.2,
        "offset_y": -5 
    },
    {
        "filename": "alimenta_cidades.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/alimenta_cidades.png",
        "link": LINK_ALIMENTA_CIDADES,
        "scale": 2.5,
        "offset_y": -25
    },
    {
        "filename": "contagem_sem_fome.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/contagem_sem_fome.png",
        "link": LINK_CONTAGEM_SEM_FOME,
        "scale": 1.0,
        "offset_y": 25
    },
    {
        "filename": "banner_pmc.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/banner_pmc.png",
        "link": PMC_PORTAL_URL,
        "scale": 1.0,
        "offset_y": 25
    }
]

####### Carregamento de imagens e database ######
@st.cache_data(show_spinner=False)
def buscar_imagem_base64(image_url: str) -> str | None:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        img_bytes = response.content
        if not img_bytes:
            print(f"Erro: Conteúdo da imagem vazio para {image_url}")
            return None
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

####### Design da página da internet e dos icones do mapa #######
ICONE_LEGENDA = {key: props["label"] for key, props in ICONES_DEFINIDOS.items()}
ICONE_PADRAO_URL = ICONES_URL_BASE + ICONE_PADRAO_ARQUIVO
LOGO_PMC_URL_CABECALHO = BANNER_URL_BASE + LOGO_PMC_FILENAME

ESTILO_POPUP = """
<div style="font-family: Arial, sans-serif; font-size: 12px; width: auto; max-width: min(90vw, 466px); min-width: 200px; word-break: break-word; box-sizing: border-box; padding: 8px;">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{}</b></h6>
    <p style="margin: 4px 0;"><b>Tipo:</b> {}</p>
    <p style="margin: 4px 0;"><b>Regional:</b> {}</p>
    {} </div>"""
ESTILO_TOOLTIP = """<div style="font-family: Arial, sans-serif; font-size: 14px"><p><b>{}:</b><br>{}</p></div>"""

####### Carregamento dos dados do mapa a partir do googledocs, do geojson com limites do município ######
@st.cache_data(ttl=600)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1qNmwcOhFnWrFHDYwkq36gHmk4Rx97b6RM0VqU94vOro/export?format=csv&gid=1832051074"
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
        return data
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_geojson():
    try:
        response = requests.get(LINK_GEOJSON, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}


def criar_legenda(geojson_data):
    regions = []
    if geojson_data and isinstance(geojson_data, dict) and 'features' in geojson_data:
        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {}); regions.append({'id': props.get('id'), 'name': props.get('Name')})
    items_legenda_regional = []
    for region in sorted(regions, key=lambda x: x.get('id', float('inf'))):
        regiao_colorida = MAPEAMENTO_CORES.get(region.get('id'), "#CCCCCC"); nome_regiao = region.get('name', 'N/A')
        if nome_regiao and nome_regiao != 'N/A' and regiao_colorida:
            items_legenda_regional.append(f"""<div style="display: flex; align-items: center; margin: 2px 0;"><div style="background: {regiao_colorida}; width: 20px; height: 20px; margin-right: 5px; border: 1px solid #ccc;"></div><span>{nome_regiao}</span></div>""")
    html_regional = f"""<div style="font-weight: bold; margin-bottom: 5px;">Regionais</div>{"".join(items_legenda_regional)}""" if items_legenda_regional else ""
    items_legenda_icones = []
    for key, props in sorted(ICONES_DEFINIDOS.items()):
        icone_url_completa = ICONES_URL_BASE + props["file"]
        icone_link_html = buscar_imagem_base64(icone_url_completa) or icone_url_completa
        legenda_texto = props["label"]
        items_legenda_icones.append(f"""<div style="display: flex; align-items: center; margin: 2px 0;"><img src="{icone_link_html}" alt="{legenda_texto}" title="{legenda_texto}" style="width: 20px; height: 20px; margin-right: 5px; object-fit: contain;"><span>{legenda_texto}</span></div>""")
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
            st.session_state.buscar_marcador = dict(zip(rounded_coords, valid_data_dict))
        except Exception as e:
            st.warning(f"Erro ao criar lookup de marcadores: {e}.");
            if 'buscar_marcador' not in st.session_state: st.session_state.buscar_marcador = {}

        feature_groups = {num: folium.FeatureGroup(name=props["label"], show=True) for num, props in ICONES_DEFINIDOS.items()}
        default_feature_group = folium.FeatureGroup(name='Outras Categorias', show=True); default_group_needed = False
        icon_base64_cache = {key: buscar_imagem_base64(ICONES_URL_BASE + props["file"]) for key, props in ICONES_DEFINIDOS.items()}
        default_icon_base64 = buscar_imagem_base64(ICONE_PADRAO_URL)

        for index, row in data.iterrows():
            if pd.isna(row["lat"]) or pd.isna(row["lon"]): continue
            lat, lon = row["lat"], row["lon"]
            icon_num = int(row["Numeral"]) if pd.notna(row["Numeral"]) else None
            icon_b64_data = icon_base64_cache.get(icon_num, default_icon_base64)
            icone_atual = folium.CustomIcon(icon_b64_data, icon_size=(25,25), icon_anchor=(0,20), popup_anchor=(0,-10)) if icon_b64_data else folium.Icon(color="green", prefix='fa', icon="leaf")
            
            popup_parts = []
            instagram_link = row.get('Instagram', '').strip()
            if instagram_link:
                link_ig_safe = instagram_link if instagram_link.startswith(('http://','https://')) else 'https://'+instagram_link
                popup_parts.append(f"<p style='margin:4px 0;'><b>Instagram:</b> <a href='{link_ig_safe}' target='_blank' rel='noopener noreferrer'>{instagram_link}</a></p>")
            
            popup_content = ESTILO_POPUP.format(row.get('Nome','N/I'), row.get('Tipo','N/I'), row.get('Regional','N/I'), "".join(popup_parts))
            popup = folium.Popup(popup_content, max_width=450)
            marker = Marker(location=[lat,lon], popup=popup, icon=icone_atual, tooltip=ESTILO_TOOLTIP.format(row.get('Tipo','N/I'), row.get('Nome','N/I')))
            
            if icon_num in feature_groups: marker.add_to(feature_groups[icon_num])
            else: marker.add_to(default_feature_group); default_group_needed = True
        
        for group in feature_groups.values(): group.add_to(m)
        if default_group_needed: default_feature_group.add_to(m)
        
    LocateControl(strings={"title":"Mostrar minha localização", "popup":"Você está aqui"}).add_to(m)
    folium.LayerControl(position='bottomleft').add_to(m)
    return m

###### Funções do streamlit para design da página e pra alocação do mapa e dos elementos do mapa #####
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="collapsed")

    
    st.markdown(
        """
        <style>
        .stApp > header {
            position: relative;
            z-index: 1000;
        }
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }
        div[data-testid="stColumns"] > div[data-testid^="stVerticalBlock"] {
            display: flex;
            flex-direction: column;
            justify-content: flex-start; 
        }
        div[data-testid="stVerticalBlock"] h3 {
            margin-top: 0px !important; 
            margin-bottom: 0px !important; 
            padding-top: 0px !important;
            padding-bottom: 0px !important;
        }
        div[data-testid="column-search-bar"] {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%; 
        }
        div[data-testid="column-PMC-logo"] {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            padding-top: 5px;
        }
        div[data-testid="column-PMC-logo"] img {
            max-width: 100%; 
            height: auto;    
            max-height: 60px;
            object-fit: contain; 
        }
        div[data-testid="column-search-bar"] .stTextInput {
            margin-top: 0px; 
            margin-bottom: 0px; 
        }
        div[data-testid="stPopover"] div[data-testid="stVerticalBlock"] {
             padding: 10px;
        }
        </style>
        """, unsafe_allow_html=True
    )

    ###### Carregamento dos elementos na sessão do usuário quando entra na página ou qunaod recarrega streamlit #########
    if 'info_marcador_selecionado' not in st.session_state: st.session_state.info_marcador_selecionado = None
    if 'valor_busca' not in st.session_state: st.session_state.valor_busca = ''
    if 'buscar_marcador' not in st.session_state: st.session_state.buscar_marcador = {}
    if 'centro_mapa' not in st.session_state: st.session_state.centro_mapa = CENTRO_INICIAL_MAPA
    if 'zoom_mapa' not in st.session_state: st.session_state.zoom_mapa = ZOOM_INICIAL_MAPA
    
    if 'df' not in st.session_state or st.session_state.df.empty:
        st.session_state.df = pd.DataFrame() 
        st.session_state.erro_processamento = False
        with st.spinner("Carregando dados..."):
            df_carregado = carregar_dados()
            if not df_carregado.empty:
                st.session_state.df = df_carregado
            else:
                st.session_state.erro_processamento = True
            st.session_state.geojson_data = carregar_geojson()
    
    ####### Layout da página ##########
    st.title(APP_TITULO)
    
    header_col1, header_col2, header_col3 = st.columns([0.6, 0.25, 0.15])

    with header_col1:
        st.header(APP_SUBTITULO)
        if st.button("Saiba Mais sobre o Projeto"):
            st.switch_page("pages/saiba_mais.py")
            
    with header_col2:
        st.markdown('<div data-testid="column-search-bar">', unsafe_allow_html=True)
        def clear_selection_on_search():
            st.session_state.info_marcador_selecionado = None

        pesquisar_unidade = st.text_input(
            "Pesquisar por Nome, Tipo ou Regional:",
            key="search_input_widget_key",
            on_change=clear_selection_on_search,
            value=st.session_state.valor_busca,
            label_visibility="collapsed"
        ).strip().lower()
        st.session_state.valor_busca = pesquisar_unidade
        st.markdown('</div>', unsafe_allow_html=True)

    with header_col3:
        st.markdown('<div data-testid="column-PMC-logo">', unsafe_allow_html=True)
        logo_bytes = get_image_bytes(LOGO_PMC_URL_CABECALHO)
        if logo_bytes:
            st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="data:image/png;base64,{base64.b64encode(logo_bytes).decode()}"></a>', unsafe_allow_html=True)
        else:
            st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="{LOGO_PMC_URL_CABECALHO}"></a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    
    with st.sidebar:
        st.header("Detalhes da Unidade")
        if st.session_state.get("info_marcador_selecionado"):
            info_selecao = st.session_state.info_marcador_selecionado
            st.subheader(info_selecao.get('Nome', 'N/I'))
            st.write(f"**Tipo:** {info_selecao.get('Tipo', 'N/I')}")
            st.write(f"**Regional:** {info_selecao.get('Regional', 'N/I')}")
            redes = info_selecao.get('Instagram', '').strip()
            if redes:
                link_ig = redes if redes.startswith(('http://','https://')) else 'https://'+redes
                st.write(f"**Instagram:**"); st.markdown(f"[{redes}]({link_ig})", unsafe_allow_html=True)
            
            info_sidebar = info_selecao.get('Info', '').strip()
            if info_sidebar:
                st.write(f"**Informações:**")
                st.markdown(info_sidebar)
            if st.button("Fechar Detalhes", key="close_sidebar_btn"):
                st.session_state.info_marcador_selecionado = None
                st.rerun()
        else:
            st.info("Clique em um marcador no mapa para ver os detalhes aqui.")

    ###### Conferir se dados existem e quebra de loop se houver falha na conexão com o googledocs ####
    df_filtrado = pd.DataFrame()
    if not st.session_state.erro_processamento and not st.session_state.df.empty:
        df_original = st.session_state.df
        if pesquisar_unidade:
            try:
                filtro_nome = df_original["Nome"].astype(str).str.contains(pesquisar_unidade, case=False, na=False, regex=False)
                filtro_tipo = df_original["Tipo"].astype(str).str.contains(pesquisar_unidade, case=False, na=False, regex=False)
                filtro_regional = df_original["Regional"].astype(str).str.contains(pesquisar_unidade, case=False, na=False, regex=False)
                df_filtrado = df_original[filtro_nome | filtro_tipo | filtro_regional]
                if df_filtrado.empty:
                    st.warning(f"Nenhuma unidade encontrada com '{pesquisar_unidade}'.")
            except Exception as e:
                st.error(f"Erro no filtro: {e}"); df_filtrado = df_original
        else:
            df_filtrado = df_original
    
    ###### Exibicação do mapa na página ###########
    if not df_filtrado.empty:
        m = criar_mapa(df_filtrado, st.session_state.get('geojson_data'))
        map_output = st_folium(
            m,
            center=st.session_state.centro_mapa,
            zoom=st.session_state.zoom_mapa,
            width='100%', height=600, key="folium_map_interactive",
            returned_objects=['last_object_clicked']
        )
    ####### Loop com função de exibir dados específicos da unidade quando clicar na unidade #####    
        if map_output and map_output.get('last_object_clicked'):
            clicked_obj = map_output['last_object_clicked']
            if clicked_obj and 'lat' in clicked_obj and 'lng' in clicked_obj:
                lat_clicada = clicked_obj['lat']; lon_clicada = clicked_obj['lng']
                coordenada_arredondada = (round(lat_clicada, 6), round(lon_clicada, 6))
                found_info = st.session_state.get('buscar_marcador', {}).get(coordenada_arredondada)
                if found_info is not None and found_info != st.session_state.info_marcador_selecionado:
                    st.session_state.info_marcador_selecionado = found_info
                    st.session_state.centro_mapa = [found_info['lat'], found_info['lon']]
                    st.session_state.zoom_mapa = ZOOM_SELECIONADO_MAPA
                    st.rerun()
            elif st.session_state.info_marcador_selecionado is not None:
                st.session_state.info_marcador_selecionado = None
                st.rerun()
                
    elif st.session_state.erro_processamento: st.error("Falha ao carregar dados. O mapa não pode ser exibido.")
    
    ###### Restante da página depois do mapa ########
    st.markdown("---"); st.caption(APP_DESC)

    
    def display_banner_html(url: str, filename: str, link_url: str | None, scale: float = 1.0, offset_y: int = 0) -> str:
        """Html do banner de rodapé."""
        escaped_url = html.escape(url)
        escaped_filename = html.escape(filename)

        base_max_height_px = 50
        scaled_max_height = int(base_max_height_px * scale)

        offset_style = f"margin-top: {offset_y}px;" if offset_y != 0 else ""

        img_style_parts = [
            "height: auto", "width: auto", "max-width: 100%",
            f"max-height: {scaled_max_height}px", "object-fit: contain",
            "display: block", "margin-left: auto", "margin-right: auto",
            offset_style
        ]
        img_style = "; ".join(filter(None, [s.strip() for s in img_style_parts]))

        image_tag = f'<img src="{escaped_url}" alt="Banner {escaped_filename}" style="{img_style}">'

        container_style_parts = [
            "display: flex", "justify-content: center", "align-items: center",
            f"min-height: {scaled_max_height}px", "overflow: hidden",
            "width: 100%", "padding: 5px",
        ]
        container_style = "; ".join(filter(None, [s.strip() for s in container_style_parts]))

        if link_url:
            return f'<div style="{container_style}"><a href="{link_url}" target="_blank" rel="noopener noreferrer">{image_tag}</a></div>'
        else:
            return f'<div style="{container_style}">{image_tag}</div>'

    cols_banner = st.columns(len(RODAPE_PAGINA))

    for i, banner_data in enumerate(RODAPE_PAGINA):
        with cols_banner[i]:
            banner_html = display_banner_html(
                url=banner_data["url"],
                filename=banner_data["filename"],
                link_url=banner_data["link"],
                scale=banner_data.get("scale", 1.0),
                offset_y=banner_data.get("offset_y", 0)
            )
            st.markdown(banner_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
