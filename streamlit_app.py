# -*- coding: utf-8 -*- # Adicionado para garantir codificação correta
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl
import logging # Para logs mais detalhados se necessário

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

# --- Templates HTML (Separados) ---

# 1. Template para o CORPO HTML do Popup (com placeholders para .format())
POPUP_HTML_BODY_TEMPLATE = """
<div style="
    font-family: Arial, sans-serif;
    font-size: 12px;
    width: auto; /* Ajusta-se ao conteúdo */
    max-width: min(90vw, 466px); /* Usa o menor entre 90% da tela e 466px */
    min-width: 200px; /* Largura mínima */
    word-break: break-word;
    box-sizing: border-box; /* Inclui padding/border no tamanho total */
    padding: 8px; /* Adiciona um respiro interno */
">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{0}</b></h6>
    <p style="margin: 4px 0;"><b>Tipo:</b> {1}</p>
    <p style="margin: 4px 0;"><b>Regional:</b> {2}</p>
    <div class="texto-curto" id="texto-curto-{3}">
        {4}
    </div>
    <div class="texto-completo" id="texto-completo-{3}" style="display: none; margin-top: 5px;">
        {5}
    </div>
    <button class="leia-mais-btn" onclick="toggleTexto('texto-curto-{3}', 'texto-completo-{3}', this)">Saiba Mais</button>
</div>
""" # NOTA: Nenhuma chave {} é escapada aqui, pois só contém placeholders para .format()

# 2. Bloco de estilo CSS (chaves {} literais)
POPUP_CSS_STYLE = """
<style>
.leia-mais-btn {
    background: none;
    border: none;
    color: #007bff; /* Azul mais padrão */
    cursor: pointer;
    padding: 0;
    font-size: 11px; /* Um pouco maior */
    margin-top: 10px; /* Mais espaço */
    display: block;
    font-weight: bold;
}
.leia-mais-btn:hover {
    text-decoration: underline;
    color: #0056b3; /* Azul mais escuro no hover */
}
</style>
""" # NOTA: As chaves {} não são escapadas aqui

# 3. Bloco de script JavaScript (chaves {} literais)
POPUP_JS_SCRIPT = """
<script>
function toggleTexto(idCurto, idCompleto, botao) {
    console.log(">> toggleTexto chamado para:", idCurto, idCompleto);

    var elementoCurto = null;
    var elementoCompleto = null;
    try {
        elementoCurto = document.getElementById(idCurto);
        elementoCompleto = document.getElementById(idCompleto);
    } catch (e) {
        console.error("!! Erro ao tentar buscar elementos por ID no popup:", e);
        return;
    }

    console.log("    Elemento Curto encontrado:", elementoCurto ? 'Sim' : 'Não');
    console.log("    Elemento Completo encontrado:", elementoCompleto ? 'Sim' : 'Não');
    console.log("    Botão encontrado:", botao ? 'Sim' : 'Não');

    if (!elementoCurto || !elementoCompleto || !botao) {
         console.error("!! Erro: Elementos não encontrados ou botão inválido dentro do popup.");
         return;
    }

    try {
        if (elementoCompleto.style.display === "none" || elementoCompleto.style.display === "") {
            console.log("    Ação: Mostrando texto completo");
            elementoCurto.style.display = "none";
            elementoCompleto.style.display = "block";
            botao.textContent = "Mostrar Menos";
        } else {
            console.log("    Ação: Mostrando texto curto");
            elementoCurto.style.display = "block";
            elementoCompleto.style.display = "none";
            botao.textContent = "Saiba Mais";
        }
         console.log("    Novos estilos:", elementoCurto.style.display, elementoCompleto.style.display);

    } catch (e) {
        console.error("!! Erro durante a troca de display ou manipulação do botão no popup:", e);
    }
}
</script>
""" # NOTA: As chaves {} não são escapadas aqui

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
        data = pd.read_csv(url, usecols=range(7))
        logging.info(f"Dados brutos carregados: {data.shape[0]} linhas.")
        # Garante que colunas essenciais não sejam nulas ANTES da conversão de tipo
        essential_cols = ['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral', 'Info']
        data.dropna(subset=essential_cols, inplace=True)
        logging.info(f"Linhas após dropna inicial: {data.shape[0]}.")

        # Conversão de tipos com tratamento de erro explícito
        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')

        # Remove linhas onde conversões falharam (resultaram em NaN)
        rows_before = data.shape[0]
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True)
        rows_after = data.shape[0]
        if rows_before > rows_after:
             logging.warning(f"{rows_before - rows_after} linhas removidas devido a valores inválidos em Numeral, lat ou lon.")

        # Converte Numeral para Int64 (permite NaN) após dropna
        data['Numeral'] = data['Numeral'].astype('Int64')

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
    return pd.DataFrame() # Retorna DataFrame vazio em caso de erro

@st.cache_data(ttl=3600)
def load_geojson():
    logging.info(f"Tentando carregar GeoJSON de: {GEOJSON_URL}")
    default_geojson = {"type": "FeatureCollection", "features": []}
    try:
        response = requests.get(GEOJSON_URL, timeout=15) # Adiciona timeout
        response.raise_for_status() # Verifica erro HTTP (4xx ou 5xx)
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
    except ValueError as e: # Captura erro de JSON inválido
        st.error(f"Erro ao decodificar GeoJSON: {e}")
        logging.error(f"Erro de decodificação JSON: {e}")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar GeoJSON: {e}")
        logging.exception("Erro inesperado no load_geojson")
    return default_geojson # Retorna default em caso de erro


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

    # Adiciona GEOJson
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
        st.warning("Não foi possível exibir a camada de regionais.")

    # Adiciona Marcadores
    max_chars = 150
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
            logging.error(f"Erro ao carregar ícone {icon_url} para {row.get('Nome', 'N/I')}: {e}. Usando ícone padrão (Folium default).")
            icon = folium.Icon(color="green", prefix='fa', icon="leaf")

        texto_completo = str(row.get('Info', 'Sem descrição detalhada.'))
        texto_curto = texto_completo[:max_chars] + ('...' if len(texto_completo) > max_chars else '')
        marker_id = f"up-{index}" # ID único para JS/HTML

        # Constrói o HTML final do popup combinando as partes
        popup_html = (
            POPUP_HTML_BODY_TEMPLATE.format(
                row.get('Nome', 'Nome não informado'), # {0}
                row.get('Tipo', 'Tipo não informado'), # {1}
                row.get('Regional', 'Regional não informada'), # {2}
                marker_id, # {3}
                texto_curto, # {4}
                texto_completo # {5}
            ) + POPUP_CSS_STYLE + POPUP_JS_SCRIPT # Concatena CSS e JS sem formatação
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

    # Adiciona Controles e Legenda
    LocateControl(strings={"title": "Mostrar minha localização", "popup": "Você está aqui"}).add_to(m)
    folium.LayerControl(position='topright').add_to(m)
    if geojson_data and geojson_data.get("features"):
       legenda = criar_legenda(geojson_data)
       m.get_root().html.add_child(legenda)
       logging.info("Legenda das regionais adicionada ao mapa.")
    else:
        logging.warning("GeoJSON inválido ou vazio, legenda das regionais não será exibida.")

    logging.info("Criação do mapa Folium concluída.")
    return m

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="collapsed")

    # Carregamento de dados
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

        # Recarrega a página uma vez após o carregamento para limpar spinners
        # (A menos que haja um erro crítico nos dados principais)
        if not st.session_state.load_error:
             st.rerun()

    # Layout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(APP_TITULO)
        st.header(APP_SUBTITULO)
    with col2:
        st.markdown(f"[![Logo PMC]({LOGO_PMC})]({LOGO_PMC})", unsafe_allow_html=True)
        search_query = st.text_input("Pesquisar por Nome:", key="search_input", value=st.session_state.get('search_input_value', '')).strip().lower()
        st.session_state.search_input_value = search_query

    # Filtragem
    df_filtrado = pd.DataFrame()
    if not st.session_state.load_error and not st.session_state.df.empty:
        df_filtrado = st.session_state.df
        if search_query:
            df_filtrado = st.session_state.df[
                st.session_state.df["Nome"].str.lower().str.contains(search_query, na=False, regex=False)
            ]
            if df_filtrado.empty:
                st.warning(f"Nenhuma unidade encontrada contendo '{search_query}' no nome.")

    # Exibição do Mapa
    if not st.session_state.load_error: # Só prossegue se os dados principais carregaram
        if not df_filtrado.empty:
            logging.info(f"Renderizando mapa com {len(df_filtrado)} unidades filtradas.")
            geojson_to_map = st.session_state.geojson_data if st.session_state.geojson_data is not None else {"type": "FeatureCollection", "features": []}
            m = criar_mapa(df_filtrado, geojson_to_map)
            st_folium(m, width='100%', height=600, key="folium_map", returned_objects=[])
        elif not search_query and not st.session_state.df.empty:
             # Dados carregaram, mas não há filtro e o DF original não está vazio
             st.info("Digite um nome na caixa de pesquisa para filtrar as unidades.")
        elif st.session_state.df.empty:
             # Os dados principais carregaram, mas a planilha estava vazia
             st.info("Nenhuma unidade produtiva encontrada nos dados carregados.")
        # O caso search_query com df_filtrado.empty já exibe um warning

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
