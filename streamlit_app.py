# -*- coding: utf-8 -*- # Adicionado para garantir codificação correta
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl
import numpy as np

# --- Configurações ---
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
APP_DESC = "Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF), em parceria com a Prefeitura Municipal de Contagem - MG"
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
ICONES = {
    1: "leaf_green.png", 2: "leaf_blue.png", 3: "leaf_orange.png", 4: "leaf_purple.png",
}
MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
    5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
}
BANNER_PMC_BASE = ["ilustracao_pmc.png", "banner_pmc.png"]
LOGO_PMC = "https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"

# --- URLs Pré-calculadas ---
ICONES_URL = {k: ICONES_URL_BASE + v for k, v in ICONES.items()}
ICONE_PADRAO = ICONES_URL_BASE + "leaf_green.png"
BANNER_PMC = [ICONES_URL_BASE + img for img in BANNER_PMC_BASE]

# --- Templates HTML (Simplificados) ---
POPUP_TEMPLATE_BASE = """
<div style="
    font-family: Arial, sans-serif;
    font-size: 12px;
    width: auto; max-width: min(90vw, 466px); min-width: 200px; /* Limitação de tamanho/resolução */
    word-break: break-word; box-sizing: border-box; padding: 8px;
">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{}</b></h6>
    <p style="margin: 4px 0;"><b>Tipo:</b> {}</p>
    <p style="margin: 4px 0;"><b>Regional:</b> {}</p>
    {}
</div>
"""

TOOLTIP_TEMPLATE = """
<div style="font-family: Arial, sans-serif; font-size: 12px">
    <p><b>Unidade Produtiva:<br>{}</b></p>
</div>
"""

# --- Funções de Carregamento de Dados ---
@st.cache_data(ttl=600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
    try:
        # Carrega as 8 primeiras colunas por índice (0 a 7).
        data = pd.read_csv(url, usecols=range(8))

        # Converte Numeral, lat, lon para numérico, tratando erros como NaN
        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')

        # Remove linhas APENAS se os dados CRUCIAIS para o mapeamento (lat, lon, Numeral) estiverem ausentes (NaN)
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True)

        # Converte Numeral para tipo inteiro que aceita NaN (Int64)
        data['Numeral'] = data['Numeral'].astype('Int64')

        # Adicionar um ID único baseado no índice do DataFrame *final* (opcional, pode ser útil)
        # data['marker_id'] = data.index.map(lambda i: f'up-{i}') # Não estritamente necessário para a lógica atual

        return data
    except pd.errors.EmptyDataError:
        st.error("O arquivo CSV da planilha parece estar vazio ou não contém cabeçalhos.")
        return pd.DataFrame()
    except ValueError as e:
        st.error(f"Erro ao processar colunas ou dados da planilha: {e}. Verifique a estrutura do CSV, os tipos de dados, e os nomes das primeiras 8 colunas.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    default_geojson = {"type": "FeatureCollection", "features": []}
    try:
        response = requests.get(GEOJSON_URL, timeout=15)
        response.raise_for_status()
        geojson_data = response.json()
        if not isinstance(geojson_data, dict) or "features" not in geojson_data:
            st.warning("Estrutura do GeoJSON inválida.")
            return default_geojson
        return geojson_data
    except requests.exceptions.Timeout:
        st.error(f"Erro ao carregar GeoJSON: Tempo limite excedido ({GEOJSON_URL})")
        return default_geojson
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de rede ao carregar GeoJSON: {e}")
        return default_geojson
    except ValueError as e:
        st.error(f"Erro ao decodificar GeoJSON: {e}")
        return default_geojson
    except Exception as e:
        st.error(f"Erro inesperado ao carregar GeoJSON: {e}")
        return default_geojson

# --- Funções de Criação do Mapa e Legenda ---
def criar_legenda(geojson_data):
    """Cria legendas nos GEOJSONs"""
    regions = []
    for feature in geojson_data.get('features', []):
        props = feature.get('properties', {})
        regions.append({
            'id': props.get('id'),
            'name': props.get('Name')
        })

    items_legenda = []
    # Ordena a legenda pelo ID da regional
    for region in sorted(regions, key=lambda x: x.get('id', float('inf'))): # Usando get com fallback seguro
        color = MAPEAMENTO_CORES.get(region.get('id'), "#fddaec")
        items_legenda.append(f"""
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="background: {color}; width: 20px; height: 20px; margin-right: 5px;"></div>
                <span>{region.get('name', 'N/A')}</span>
            </div>
        """)

    return folium.Element(f"""
        <div style="
            position: fixed;
            bottom: 50px;
            right: 20px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.85);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            font-family: Arial;
            font-size: 12px;
            max-width: 150px;
        ">
            <div style="font-weight: bold; margin-bottom: 5px;">Regionais</div>
            {"".join(items_legenda)}
        </div>
    """)

def criar_mapa(data, geojson_data):
    m = folium.Map(location=[-19.8888, -44.0535], tiles="cartodbpositron",
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

    if isinstance(data, pd.DataFrame) and not data.empty:
        coord_precision = 6
        try:
            valid_coords = data[['lat', 'lon']].apply(pd.to_numeric, errors='coerce').dropna()
            rounded_coords = list(zip(np.round(valid_coords['lat'], coord_precision),
                                      np.round(valid_coords['lon'], coord_precision)))
            valid_data_dict = data.loc[valid_coords.index].to_dict('records')
            st.session_state.marker_lookup = dict(zip(rounded_coords, valid_data_dict))
        except Exception as e:
             st.warning(f"Erro ao criar o dicionário de lookup de marcadores: {e}. A seleção por clique pode falhar.")
             st.session_state.marker_lookup = {}

        for index, row in data.iterrows():
            if pd.isna(row["lat"]) or pd.isna(row["lon"]):
                 continue

            lat, lon = row["lat"], row["lon"]
            icon_num = row["Numeral"]

            try:
                icon_url = ICONES_URL.get(int(icon_num), ICONE_PADRAO)
            except (ValueError, TypeError):
                icon_url = ICONE_PADRAO

            try:
                icon = folium.CustomIcon(icon_url, icon_size=(30, 30), icon_anchor=(-30, 15), popup_anchor=(0, -10))
            except Exception as e:
                st.warning(f"Erro ao carregar ícone {icon_url} para {row.get('Nome', 'N/I')}: {e}. Usando ícone padrão.")
                icon = folium.Icon(color="green", prefix='fa', icon="leaf")

            # --- Construção dinâmica do HTML do popup (SEM A SEÇÃO 'Info') ---
            popup_parts = [] # Inicializa lista para partes do popup

            # Bloco que adicionava 'Info' foi REMOVIDO daqui:
            # info_text = row.get('Info')
            # if pd.notna(info_text) and str(info_text).strip() != '':
            #    popup_parts.append(f"<p style='margin: 4px 0;'><b>Informações:</b></p><p style='margin: 4px 0;'>{info_text}</p>")

            # Mantém a lógica para Instagram (se existir)
            instagram_link = row.get('Instagram')
            if pd.notna(instagram_link) and isinstance(instagram_link, str) and instagram_link.strip() != '':
                 instagram_link_safe = instagram_link.strip()
                 if not instagram_link_safe.startswith(('http://', 'https://')):
                      instagram_link_safe = 'https://' + instagram_link_safe
                 popup_parts.append(f"<p style='margin: 4px 0;'><b>Instagram:</b> <a href='{instagram_link_safe}' target='_blank'>{instagram_link.strip()}</a></p>")

            # Formata o template base apenas com as partes restantes (Nome, Tipo, Regional, Instagram)
            popup_content = POPUP_TEMPLATE_BASE.format(
                row.get('Nome', 'Nome não informado'),
                row.get('Tipo', 'Tipo não informado'),
                row.get('Regional', 'Regional não informada'),
                "".join(popup_parts) # Junta as partes (agora sem 'Info')
            )
            popup = folium.Popup(popup_content, max_width=500)

            Marker(
                location=[lat, lon],
                popup=popup, # Popup agora sem a seção 'Info'
                icon=icon,
                tooltip=TOOLTIP_TEMPLATE.format(row.get('Nome', 'N/I'))
            ).add_to(m)

    LocateControl(strings={"title": "Mostrar minha localização", "popup": "Você está aqui"}).add_to(m)
    folium.LayerControl(position='topright').add_to(m)
    if geojson_data and geojson_data.get("features"):
        legenda = criar_legenda(geojson_data)
        m.get_root().html.add_child(legenda)

    return m

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="expanded") # Expandido para ver melhor no início

    # Inicializa o estado para a informação da unidade selecionada, o valor da busca, e o dicionário de lookup
    if 'selected_marker_info' not in st.session_state:
        st.session_state.selected_marker_info = None
    if 'search_input_value' not in st.session_state:
        st.session_state.search_input_value = ''
    if 'marker_lookup' not in st.session_state:
        st.session_state.marker_lookup = {} # Dicionário de lookup inicializado
    if 'data_loaded' not in st.session_state:
         st.session_state.data_loaded = False # Controle para carregamento inicial
         st.session_state.load_error = False
         st.session_state.df = pd.DataFrame()
         st.session_state.geojson_data = None


    # --- Carregamento de Dados Inicial (apenas uma vez ou quando cache expira) ---
    if not st.session_state.data_loaded:
        with st.spinner("Carregando dados das unidades..."):
            loaded_df = load_data()
            if not loaded_df.empty:
                st.session_state.df = loaded_df
            else:
                st.session_state.load_error = True

        with st.spinner("Carregando mapa das regionais..."):
            geojson = load_geojson()
            if geojson and geojson.get("features"):
                st.session_state.geojson_data = geojson
            # Não definir load_error aqui, o mapa pode funcionar sem GeoJSON

        st.session_state.data_loaded = True # Marca que os dados foram carregados

    # --- Layout Principal ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(APP_TITULO)
        st.header(APP_SUBTITULO)
    with col2:
        st.image(LOGO_PMC, width=150) # Usar st.image para controle de tamanho
        # Usar um callback para limpar a seleção ao mudar a busca
        def clear_selection_on_search():
             st.session_state.selected_marker_info = None
             # Mantem o valor da busca atualizado no estado
             st.session_state.search_input_value = st.session_state.search_input_widget

        search_query = st.text_input("Pesquisar por Nome:",
                                     key="search_input_widget",
                                     on_change=clear_selection_on_search,
                                     value=st.session_state.search_input_value).strip().lower()

    # --- Lógica da Sidebar (Executada a cada re-run *antes* do mapa) ---
    with st.sidebar:
        st.title("Detalhes da Unidade")
        # A sidebar lê o valor de selected_marker_info que foi definido na re-execução ANTERIOR
        if st.session_state.selected_marker_info:
            info = st.session_state.selected_marker_info
            st.header(info.get('Nome', 'Nome não informado'))
            st.write(f"**Tipo:** {info.get('Tipo', 'Tipo não informado')}")
            st.write(f"**Regional:** {info.get('Regional', 'Regional não informada')}")

            redes = info.get('Instagram')
            if pd.notna(redes) and isinstance(redes, str) and redes.strip() != "":
                 link_ig = redes.strip()
                 if not link_ig.startswith(('http://', 'https://')):
                      link_ig = 'https://' + link_ig
                 st.write(f"**Instagram:** [Link]({link_ig})")

            info_text_sidebar = info.get('Info')
            if pd.notna(info_text_sidebar) and str(info_text_sidebar).strip() != '':
                st.write(f"**Informações:**")
                st.markdown(info_text_sidebar)
        else:
            # Estado inicial ou após limpar a seleção (ex: nova busca, clique fora de marcador)
            st.info("Clique em um marcador no mapa para ver os detalhes aqui.")


    # --- Filtragem (baseado na busca atual) ---
    df_filtrado = pd.DataFrame()
    # Usa o DataFrame carregado no estado da sessão
    if not st.session_state.load_error and not st.session_state.df.empty:
        df_original = st.session_state.df
        if 'Nome' in df_original.columns and search_query:
            # Aplica filtro se houver busca
            df_filtrado = df_original[
                df_original["Nome"].str.lower().str.contains(search_query, na=False, regex=False)
            ]
            if df_filtrado.empty:
                st.warning(f"Nenhuma unidade encontrada contendo '{search_query}' no nome.")
        elif search_query:
            # Se busca foi feita mas coluna Nome não existe
            st.warning("A coluna 'Nome' não foi encontrada nos dados, a busca não pôde ser aplicada.")
            df_filtrado = pd.DataFrame() # Garante dataframe vazio
        else:
            # Sem busca, usa todos os dados
            df_filtrado = df_original
    # Se houve erro de carga ou df original está vazio, df_filtrado continua vazio


    # --- Exibição do Mapa e Processamento do Clique (Executado *depois* da sidebar) ---
    if not df_filtrado.empty: # Só exibe mapa se houver dados (originais ou filtrados)
        geojson_to_map = st.session_state.geojson_data if st.session_state.geojson_data is not None else {"type": "FeatureCollection", "features": []}

        # Cria o mapa com os dados filtrados. Importante: o lookup é (re)criado aqui.
        m = criar_mapa(df_filtrado, geojson_to_map)

        # Renderiza o mapa. `map_output` receberá o resultado da interação (ex: clique) da *última* interação.
        map_output = st_folium(m, width='100%', height=600, key="folium_map", returned_objects=['last_object_clicked'])

        # --- Lógica para Capturar Clique e Atualizar Sidebar para a *PRÓXIMA* re-execução ---
        # map_output contém dados se houve um clique na interação anterior que causou esta re-execução.
        if map_output and map_output.get('last_object_clicked'):
            clicked_obj = map_output['last_object_clicked']

            # Verifica se o clique foi em um marcador (tem lat/lon)
            if 'lat' in clicked_obj and 'lng' in clicked_obj:
                clicked_lat = clicked_obj['lat']
                clicked_lon = clicked_obj['lng']

                # --- Usa o dicionário de lookup (que foi atualizado em criar_mapa com df_filtrado) ---
                coord_precision = 6 # Mesma precisão usada em criar_mapa
                clicked_key = (round(clicked_lat, coord_precision), round(clicked_lon, coord_precision))

                # Procura no lookup atual. Se encontrar, ATUALIZA o session_state.
                # Esta atualização será lida pela sidebar na PRÓXIMA re-execução.
                found_info = st.session_state.marker_lookup.get(clicked_key)
                if found_info:
                     # Compara com o estado atual para evitar re-runs desnecessários se o mesmo marcador for clicado novamente
                     if st.session_state.selected_marker_info != found_info:
                          st.session_state.selected_marker_info = found_info
                          # Força um rerun IMEDIATO para que a sidebar atualize "instantaneamente" (na verdade, é um novo rerun)
                          # Isso pode ou não ser desejável dependendo da complexidade do app
                          st.rerun()
                else:
                     # Se o clique foi em um local válido (lat/lon) mas não correspondeu a um marcador no lookup atual
                     # (pode acontecer se o filtro mudou entre o clique e o rerun)
                     if st.session_state.selected_marker_info is not None:
                         st.session_state.selected_marker_info = None
                         st.rerun() # Limpa a sidebar

            else:
                # Clique em outra coisa (ex: GeoJSON) ou fora de tudo. Limpa a seleção.
                if st.session_state.selected_marker_info is not None:
                     st.session_state.selected_marker_info = None
                     st.rerun() # Limpa a sidebar
        # Se não houve clique nesta interação (map_output['last_object_clicked'] é None),
        # st.session_state.selected_marker_info mantém seu valor anterior.

    elif st.session_state.load_error:
        # Mensagem de erro já foi mostrada em load_data
        st.error("Falha ao carregar os dados das unidades. Não é possível exibir o mapa.")
    elif not st.session_state.df.empty and df_filtrado.empty and search_query:
        # Dados carregados, mas filtro não encontrou nada (warning já exibido)
        pass # Não precisa mostrar mais nada
    else: # Caso inicial (sem dados) ou outros casos não cobertos
         if not search_query: # Só mostra se não for resultado de uma busca vazia
             st.info("Não há unidades produtivas para exibir no mapa.")


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
