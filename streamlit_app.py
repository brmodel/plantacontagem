# -*- coding: utf-8 -*- # Adicionado para garantir codificação correta
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl
import logging # Para logs mais detalhados se necessário
import numpy as np # Para comparações de ponto flutuante seguras

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)

# --- Configurações ---
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
APP_DESC = "Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF), em parceria com a Prefeitura Municipal de Contagem - MG"
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
ICONES = {
    1: "leaf_green.png", 2: "leaf_orange.png", 3: "leaf_blue.png", 4: "leaf_purple.png",
}
MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
    5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
}
BANNER_PMC_BASE = ["ilustracao_pmc.png", "banner_pmc.png"]
LOGO_PMC = "https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"

# --- Precomputed URLs ---
ICONES_URL = {k: ICONES_URL_BASE + v for k, v in ICONES.items()}
ICONE_PADRAO = ICONES_URL_BASE + "leaf_green.png"
BANNER_PMC = [ICONES_URL_BASE + img for img in BANNER_PMC_BASE]

# --- Templates HTML (Simplificados) ---

# Template para o Popup (apenas info básica, SEM botão "Saiba Mais" ou JS/CSS inline)
# REMOVIDOS os comentários Python dentro das chaves de formatação {}
POPUP_TEMPLATE = """
<div style="
    font-family: Arial, sans-serif;
    font-size: 12px;
    width: auto; max-width: min(90vw, 466px); min-width: 200px; /* Limitação de tamanho/resolução */
    word-break: break-word; box-sizing: border-box; padding: 8px;
">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{0}</b></h6>
    <p style="margin: 4px 0;"><b>Tipo:</b> {1}</p>
    <p style="margin: 4px 0;"><b>Regional:</b> {2}</p>
</div>
""" # Sem botão, sem JS, sem estilos específicos aqui. Comentários /* */ removidos das chaves.

TOOLTIP_TEMPLATE = """
<div style="font-family: Arial, sans-serif; font-size: 12px">
    <p><b>Unidade Produtiva:<br>{}</b></p>
</div>
"""

# --- Funções de Carregamento de Dados ---
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
    logging.info(f"Tentando carregar dados de: {url}")
    try:
        data = pd.read_csv(url, usecols=range(8))
        logging.info(f"Dados brutos carregados: {data.shape[0]} linhas.")
        essential_cols = ['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral', 'Info', 'Redes Sociais']
        data.dropna(subset=essential_cols, inplace=True)
        logging.info(f"Linhas após dropna inicial: {data.shape[0]}.")

        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')

        rows_before = data.shape[0]
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True)
        rows_after = data.shape[0]
        if rows_before > rows_after:
             logging.warning(f"{rows_before - rows_after} linhas removidas devido a valores inválidos em Numeral, lat ou lon.")

        data['Numeral'] = data['Numeral'].astype('Int64')

        # Adicionar um ID único baseado no índice para facilitar a lookup
        data['marker_id'] = data.index.map(lambda i: f'up-{i}')

        logging.info(f"Dados limpos carregados: {data.shape[0]} linhas.")
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de rede ao buscar dados da planilha: {e}")
        logging.error(f"Erro de rede ao buscar dados: {e}")
    except pd.errors.ParserError as e:
        st.error(f"Erro ao processar o arquivo CSV da planilha: {e}")
        logging.error(f"Erro de parser CSV: {e}")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar dados: {e}")
        logging.exception("Erro inesperado no load_data")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    logging.info(f"Tentando carregar GeoJSON de: {GEOJSON_URL}")
    default_geojson = {"type": "FeatureCollection", "features": []}
    try:
        response = requests.get(GEOJSON_URL, timeout=15)
        response.raise_for_status()
        geojson_data = response.json()
        if not isinstance(geojson_data, dict) or "features" not in geojson_data:
            st.warning("Estrutura do GeoJSON inválida.")
            logging.warning("Estrutura do GeoJSON inválida.")
            return default_geojson
        logging.info(f"GeoJSON carregado com {len(geojson_data.get('features', []))} features.")
        return geojson_data
    except requests.exceptions.Timeout:
        st.error(f"Erro ao carregar GeoJSON: Tempo limite excedido ({GEOJSON_URL})")
        logging.error("Timeout ao carregar GeoJSON.")
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de rede ao carregar GeoJSON: {e}")
        logging.error(f"Erro de rede GeoJSON: {e}")
    except ValueError as e:
        st.error(f"Erro ao decodificar GeoJSON: {e}")
        logging.error(f"Erro de decodificação JSON: {e}")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar GeoJSON: {e}")
        logging.exception("Erro inesperado no load_geojson")
    return default_geojson


# --- Funções de Criação do Mapa e Legenda ---
def criar_legenda(geojson_data):
    regions = []
    features = geojson_data.get('features') if isinstance(geojson_data, dict) else None
    if isinstance(features, list):
        for feature in features:
            props = feature.get('properties') if isinstance(feature, dict) else {}
            if isinstance(props, dict):
                 region_id = props.get('id')
                 region_name = props.get('Name')
                 if isinstance(region_id, (int, float)) and region_name is not None:
                     regions.append({'id': int(region_id), 'name': region_name})
                 elif region_id is not None and region_name is not None:
                     logging.warning(f"ID da regional '{region_id}' não é numérico. Ignorando na legenda.")

    items_legenda = []
    for region in sorted(regions, key=lambda x: x.get('id', float('inf'))):
        color = MAPEAMENTO_CORES.get(region.get('id'), "#cccccc")
        items_legenda.append(f"""
            <div style="display: flex; align-items: center; margin: 3px 0;">
                <div style="background: {color}; width: 18px; height: 18px; margin-right: 6px; border: 1px solid #999; flex-shrink: 0;"></div>
                <span style="font-size: 11px;">{region.get('name', 'N/A')}</span>
            </div>
        """)

    return folium.Element(f"""
        <div style="
            position: fixed; bottom: 40px; right: 10px; z-index: 1000;
            background: rgba(255, 255, 255, 0.85); padding: 8px 12px;
            border-radius: 5px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif; max-width: 160px; max-height: 250px;
            overflow-y: auto; font-size: 12px;
        ">
            <div style="font-weight: bold; margin-bottom: 5px; font-size: 13px;">Regionais</div>
            {"".join(items_legenda)}
        </div>
    """)

def criar_mapa(data, geojson_data):
    logging.info("Iniciando criação do mapa Folium.")
    m = folium.Map(location=[-19.9208, -44.0535], tiles="cartodbpositron",
                   zoom_start=12, control_scale=True)

    if geojson_data and geojson_data.get("features"):
        folium.GeoJson(
            geojson_data, name='Regionais',
            style_function=lambda x: {
                "fillColor": MAPEAMENTO_CORES.get(x['properties'].get('id'), "#cccccc"),
                "color": "#555555", "weight": 1, "fillOpacity": 0.3,
            },
            tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
            highlight_function=lambda x: {"weight": 2, "fillOpacity": 0.5, "color": "black"},
            interactive=True, control=True, show=True
        ).add_to(m)
        logging.info("Camada GeoJSON adicionada ao mapa.")
    else:
        logging.warning("Dados GeoJSON não disponíveis ou vazios para adicionar ao mapa.")

    marker_count = 0
    for index, row in data.iterrows():
        lat, lon = row.get("lat"), row.get("lon")
        if pd.isna(lat) or pd.isna(lon) or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            logging.warning(f"Coordenadas inválidas ou ausentes para {row.get('Nome', 'N/I')} (Índice: {index}). Pulando marcador.")
            continue

        icon_num = row.get("Numeral")
        icon_url = ICONES_URL.get(icon_num, ICONE_PADRAO)
        try:
            icon = folium.CustomIcon(icon_url, icon_size=(30, 30), icon_anchor=(15, 15), popup_anchor=(0, -10))
        except Exception as e:
            logging.error(f"Erro ao carregar ícone {icon_url} para {row.get('Nome', 'N/I')}: {e}. Usando ícone padrão.")
            icon = folium.Icon(color="green", prefix='fa', icon="leaf")

        # Formata o HTML simples do popup (sem botão ou JS)
        # Garantindo que o get() tem um fallback caso a coluna não exista por algum motivo (segurança)
        popup_html = POPUP_TEMPLATE.format(
            row.get('Nome', 'Nome não informado'), # {0}
            row.get('Tipo', 'Tipo não informado'), # {1}
            row.get('Regional', 'Regional não informada') # {2}
        )

        popup = folium.Popup(popup_html, max_width=500)

        Marker(
            location=[lat, lon],
            popup=popup,
            icon=icon,
            tooltip=TOOLTIP_TEMPLATE.format(row.get('Nome', 'N/I'))
        ).add_to(m)
        marker_count += 1

    logging.info(f"{marker_count} marcadores adicionados ao mapa.")

    LocateControl(strings={"title": "Mostrar minha localização", "popup": "Você está aqui"}).add_to(m)
    folium.LayerControl(position='topright').add_to(m)
    if geojson_data and geojson_data.get("features"):
       legenda = criar_legenda(geojson_data)
       m.get_root().html.add_child(legenda)
       logging.info("Legenda das regionais adicionada ao mapa.")

    logging.info("Criação do mapa Folium concluída.")
    return m

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="collapsed")

    # Inicializa o estado para a informação da unidade selecionada
    if 'selected_marker_info' not in st.session_state:
        st.session_state.selected_marker_info = None
    # Inicializa o estado para o valor da busca
    if 'search_input_value' not in st.session_state:
        st.session_state.search_input_value = ''

    if 'data_loaded' not in st.session_state:
        st.session_state.load_error = False
        with st.spinner("Carregando dados das unidades..."):
            st.session_state.df = load_data()
            if st.session_state.df.empty:
                 st.session_state.load_error = True

        st.session_state.geojson_data = None
        with st.spinner("Carregando mapa das regionais..."):
             geojson = load_geojson()
             if geojson and geojson.get("features"):
                 st.session_state.geojson_data = geojson
             else:
                 logging.warning("GeoJSON não carregado ou inválido.")
                 st.warning("Não foi possível carregar os dados das regionais para o mapa.")

        st.session_state.data_loaded = True

        # Não recarrega automaticamente após o carregamento inicial
        # A interação com o mapa (clique) irá disparar os reruns necessários.

    # --- Layout Principal (Colunas) ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(APP_TITULO)
        st.header(APP_SUBTITULO)
    with col2:
        st.markdown(f"[![Logo PMC]({LOGO_PMC})]({LOGO_PMC})", unsafe_allow_html=True)
        search_query = st.text_input("Pesquisar por Nome:", key="search_input", value=st.session_state.search_input_value).strip().lower()
        st.session_state.search_input_value = search_query # Atualiza o estado com o valor atual

    # --- Lógica da Sidebar ---
    # A sidebar deve ser definida ANTES da chamada st_folium para que ela exista no primeiro rerun
    # mesmo antes de qualquer clique.
    st.sidebar.title("Detalhes da Unidade")
    # Verifica se há informação de marcador selecionado no estado
    if st.session_state.selected_marker_info:
        info = st.session_state.selected_marker_info
        # Exibe as informações completas na sidebar
        st.sidebar.header(info.get('Nome', 'Nome não informado'))
        st.sidebar.write(f"**Tipo:** {info.get('Tipo', 'Tipo não informado')}")
        st.sidebar.write(f"**Regional:** {info.get('Regional', 'Regional não informada')}")
        st.sidebar.write(f"**Informações:**")
        st.sidebar.write(info.get('Info', 'Sem descrição detalhada.'))
    else:
        st.sidebar.info("Clique em um marcador no mapa para ver os detalhes aqui.") # Texto de instrução atualizado

    # --- Filtragem ---
    df_filtrado = pd.DataFrame()
    if not st.session_state.load_error and not st.session_state.df.empty:
        df_filtrado = st.session_state.df
        if search_query:
            df_filtrado = st.session_state.df[
                st.session_state.df["Nome"].str.lower().str.contains(search_query, na=False, regex=False)
            ]
            if df_filtrado.empty:
                st.warning(f"Nenhuma unidade encontrada contendo '{search_query}' no nome.")

    # --- Exibição do Mapa ---
    # O mapa só é exibido se não houver erro crítico nos dados principais
    if not st.session_state.load_error:
        if not df_filtrado.empty:
            logging.info(f"Renderizando mapa com {len(df_filtrado)} unidades filtradas.")
            # Passa o geojson_data. Se geojson falhou, passa um objeto vazio seguro.
            geojson_to_map = st.session_state.geojson_data if st.session_state.geojson_data is not None else {"type": "FeatureCollection", "features": []}
            m = criar_mapa(df_filtrado, geojson_to_map)
            # st_folium renderiza o mapa e retorna o estado da interação.
            # Retornamos 'last_object_clicked' para pegar o lat/lon do clique em marcadores ou GeoJson.
            map_output = st_folium(m, width='100%', height=600, key="folium_map", returned_objects=['last_object_clicked'])

            # --- Lógica para Capturar Clique e Atualizar Sidebar ---
            # Verifica se um objeto no mapa foi clicado (retornado por st_folium)
            if map_output and map_output.get('last_object_clicked'):
                clicked_obj = map_output['last_object_clicked']
                logging.info(f"Objeto clicado no mapa: {clicked_obj}")

                # Verifica se o objeto clicado tem coordenadas (marcadores e feições GeoJson pontuais/centroides)
                if 'lat' in clicked_obj and 'lng' in clicked_obj:
                    clicked_lat = clicked_obj['lat']
                    clicked_lon = clicked_obj['lng']
                    logging.info(f"Clique detectado em Lat: {clicked_lat}, Lon: {clicked_lon}")

                    # Tenta encontrar a linha do DataFrame que corresponde a estas coordenadas
                    found_row = None
                    # Iteramos sobre as linhas do DataFrame filtrado atualmente exibido no mapa
                    # Isso é mais eficiente do que buscar no DF completo se houver muitos dados e filtro ativo.
                    # Se um item for clicado, ele DEVE estar no df_filtrado.
                    for index, row in df_filtrado.iterrows():
                         # Compara as coordenadas do clique com as coordenadas da linha usando tolerância
                         # Usamos um tolerance razoável para imprecisões de ponto flutuante.
                         if np.isclose(row['lat'], clicked_lat, atol=1e-6) and np.isclose(row['lon'], clicked_lon, atol=1e-6):
                             found_row = row
                             logging.info(f"Encontrada linha correspondente (Índice: {index}) para o clique Lat/Lon.")
                             break # Encontramos a linha correspondente, saímos do loop

                    if found_row is not None:
                        # Armazena as informações completas da linha encontrada no session_state
                        # O .to_dict() converte a Série Pandas (linha do DF) para um dicionário
                        st.session_state.selected_marker_info = found_row.to_dict()
                        logging.info("Sidebar info atualizada no session_state com dados do clique.")
                        # Streamlit detecta a mudança no session_state e dispara um rerun automaticamente
                        # (Não precisamos chamar st.rerun() explicitamente aqui)
                    else:
                         logging.warning(f"Clique em Lat: {clicked_lat}, Lon: {clicked_lon} não correspondeu a nenhuma linha no DF filtrado.Sidebar não atualizada.")
                         # Opcional: Limpar a sidebar se o clique não for em um marcador conhecido
                         # st.session_state.selected_marker_info = None # Limpa se não encontrar

        elif not search_query and not st.session_state.df.empty:
             # Caso não haja filtro de busca e o DF original não está vazio, mas df_filtrado está (situação rara)
             st.info("Digite um nome na caixa de pesquisa para filtrar as unidades.")
        elif st.session_state.df.empty:
             # Os dados principais carregaram, mas a planilha estava vazia desde o início
             st.info("Nenhuma unidade produtiva encontrada nos dados carregados.")
        # O caso search_query com df_filtrado.empty já exibe um warning em 'Filtragem'


    # Rodapé
    st.markdown("---")
    st.caption(APP_DESC)
    if len(BANNER_PMC) > 1:
        cols_banner = st.columns(len(BANNER_PMC))
        for i, url in enumerate(BANNER_PMC):
            with cols_banner[i]:
                st.image(url, use_container_width=True)
    elif BANNER_PMC:
        st.image(BANNER_PMC[0], use_container_width=True)

if __name__ == "__main__":
    main()
