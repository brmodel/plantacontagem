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
    1: "leaf_green.png", 2: "leaf_orange.png", 3: "leaf_blue.png", 4: "leaf_purple.png",
}
MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
    5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
}
BANNER_PMC_BASE = ["ilustracao_pmc.png", "banner_pmc.png"]
LOGO_PMC = "https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"

# Lista de colunas essenciais - usada para carregar e validar.
essential_cols = ['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral', 'Info', 'Instagram']


# --- URLs Pré-calculadas ---
ICONES_URL = {k: ICONES_URL_BASE + v for k, v in ICONES.items()}
ICONE_PADRAO = ICONES_URL_BASE + "leaf_green.png"
BANNER_PMC = [ICONES_URL_BASE + img for img in BANNER_PMC_BASE]

# --- Templates HTML (Simplificados) ---
# Template base para o popup, sem placeholders fixos para Info e Instagram
POPUP_TEMPLATE_BASE = """
<div style="
    font-family: Arial, sans-serif;
    font-size: 12px;
    width: auto; max-width: min(90vw, 466px); min-width: 200px; /* Limitação de tamanho/resolução */
    word-break: break-word; box-sizing: border-box; padding: 8px;
">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{}</b></h6> <p style="margin: 4px 0;"><b>Tipo:</b> {}</p> <p style="margin: 4px 0;"><b>Regional:</b> {}</p> {} </div>
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
        data = pd.read_csv(url, usecols=range(8))

        # Verifica se todas as colunas essenciais foram carregadas com os nomes esperados
        if not all(col in data.columns for col in essential_cols):
             missing_cols = [col for col in essential_cols if col not in data.columns]
             st.error(f"Erro: As colunas essenciais {missing_cols} não foram encontradas no CSV carregado. Verifique os nomes e a ordem das primeiras 8 colunas na planilha.")
             return pd.DataFrame()

        # Converte Numeral, lat, lon para numérico, tratando erros como NaN
        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')

        # Remove linhas APENAS se os dados CRUCIAIS para o mapeamento (lat, lon, Numeral) estiverem ausentes (NaN)
        rows_before_mapping_dropna = data.shape[0]
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True)
        rows_after_mapping_dropna = data.shape[0]
        if rows_before_mapping_dropna > rows_after_mapping_dropna:
             pass # Aviso removido

        # Converte Numeral para tipo inteiro que aceita NaN (Int64)
        data['Numeral'] = data['Numeral'].astype('Int64')

        # Adicionar um ID único baseado no índice do DataFrame *final*
        data['marker_id'] = data.index.map(lambda i: f'up-{i}')

        # As colunas 'Info' e 'Instagram' agora podem conter NaNs, mas o código
        # que as acessa na sidebar/popup (usando .get()) lida com isso.

        return data
    except pd.errors.EmptyDataError:
        st.error("O arquivo CSV da planilha parece estar vazio ou não contém cabeçalhos.")
        return pd.DataFrame()
    except ValueError as e:
        st.error(f"Erro ao processar colunas ou dados da planilha: {e}. Verifique a estrutura do CSV, os tipos de dados, E SE OS NOMES DAS COLUNAS EM essential_cols correspondem ao cabeçalho das primeiras 8 colunas do CSV.")
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
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de rede ao carregar GeoJSON: {e}")
    except ValueError as e:
        st.error(f"Erro ao decodificar GeoJSON: {e}")
    except Exception as e:
        st.error(f"Erro inesperado ao carregar GeoJSON: {e}")
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
                    st.warning(f"ID da regional '{region_id}' não é numérico. Ignorando na legenda.")


    items_legenda = []
    # Ordena a legenda pelo ID da regional
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
    else:
        pass

    marker_count = 0
    if isinstance(data, pd.DataFrame) and not data.empty:
        for index, row in data.iterrows():
            # Graças à dropna(['Numeral', 'lat', 'lon']), estas colunas devem existir e ser numéricas não NaN aqui.
            lat, lon = row["lat"], row["lon"]
            icon_num = row["Numeral"]

            # Acesso seguro ao dicionário ICONES_URL, convertendo Numeral para int
            try:
                icon_url = ICONES_URL.get(int(icon_num), ICONE_PADRAO)
            except (ValueError, TypeError):
                icon_url = ICONE_PADRAO


            try:
                # Note: row.get('Nome', 'N/I') usado aqui e no tooltip para lidar com caso Nome tenha NaN
                icon = folium.CustomIcon(icon_url, icon_size=(30, 30), icon_anchor=(15, 15), popup_anchor=(0, -10))
            except Exception as e:
                st.error(f"Erro ao carregar ícone {icon_url} para {row.get('Nome', 'N/I')}: {e}. Usando ícone padrão.")
                icon = folium.Icon(color="green", prefix='fa', icon="leaf")

            # --- Construção dinâmica do HTML do popup ---
            # Começa com a parte base (Nome, Tipo, Regional)
            # Note: row.get() usado com fallback caso Nome, Tipo, Regional sejam NaN (embora dropna(['Numeral',...])
            # não garanta isso para Nome, Tipo, Regional, usar get é seguro)
            popup_content = POPUP_TEMPLATE_BASE.format(
                row.get('Nome', 'Nome não informado'),
                row.get('Tipo', 'Tipo não informado'),
                row.get('Regional', 'Regional não informada'),
                '' # Placeholder inicial vazio para o conteúdo condicional
            )

            # Adiciona Informações se existirem e não forem vazias/NaN
            info_text = row.get('Info')
            if pd.notna(info_text) and str(info_text).strip() != '':
                 popup_content = popup_content.replace('{}', f"<p style='margin: 4px 0;'><b>Informações:</b></p><p style='margin: 4px 0;'>{info_text}</p>" + '{}')

            # Adiciona Instagram se existir e não for vazio/NaN
            instagram_link = row.get('Instagram')
            if pd.notna(instagram_link) and isinstance(instagram_link, str) and instagram_link.strip() != '':
                 popup_content = popup_content.replace('{}', f"<p style='margin: 4px 0;'><b>Instagram:</b> <a href='{instagram_link.strip()}' target='_blank'>{instagram_link.strip()}</a></p>" + '{}')

            # Remove o placeholder final vazio se nada condicional foi adicionado
            popup_html = popup_content.replace('{}', '')

            popup = folium.Popup(popup_html, max_width=500)

            Marker(
                location=[lat, lon],
                popup=popup,
                icon=icon,
                tooltip=TOOLTIP_TEMPLATE.format(row.get('Nome', 'N/I')) # Usa get para Nome no tooltip também
            ).add_to(m)
            marker_count += 1

    LocateControl(strings={"title": "Mostrar minha localização", "popup": "Você está aqui"}).add_to(m)
    folium.LayerControl(position='topright').add_to(m)
    if geojson_data and geojson_data.get("features"):
        legenda = criar_legenda(geojson_data)
        m.get_root().html.add_child(legenda)

    return m

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="collapsed")

    if 'selected_marker_info' not in st.session_state:
        st.session_state.selected_marker_info = None
    if 'search_input_value' not in st.session_state:
        st.session_state.search_input_value = ''

    # --- Carregamento de Dados Inicial ---
    if 'data_loaded' not in st.session_state:
        st.session_state.load_error = False
        st.session_state.df = pd.DataFrame()
        st.session_state.geojson_data = None

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
            else:
                st.warning("Não foi possível carregar os dados das regionais para o mapa.")

        st.session_state.data_loaded = True

    # --- Layout Principal ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(APP_TITULO)
        st.header(APP_SUBTITULO)
    with col2:
        st.markdown(f"[![Logo PMC]({LOGO_PMC})]({LOGO_PMC})", unsafe_allow_html=True)
        search_query = st.text_input("Pesquisar por Nome:", key="search_input_widget",
                                     value=st.session_state.search_input_value).strip().lower()

        if search_query != st.session_state.search_input_value:
            st.session_state.search_input_value = search_query

    # --- Lógica da Sidebar ---
    with st.sidebar:
        st.title("Detalhes da Unidade")
        if st.session_state.selected_marker_info:
            info = st.session_state.selected_marker_info
            st.header(info.get('Nome', 'Nome não informado'))
            st.write(f"**Tipo:** {info.get('Tipo', 'Tipo não informado')}")
            st.write(f"**Regional:** {info.get('Regional', 'Regional não informada')}")

            # Exibe Instagram apenas se existir e não for vazio/NaN
            redes = info.get('Instagram')
            if pd.notna(redes) and isinstance(redes, str) and redes.strip() != "":
                st.write(f"**Instagram:** [Link]({redes.strip()})")

            # Exibe Informações apenas se existirem e não forem vazias/NaN
            info_text_sidebar = info.get('Info')
            if pd.notna(info_text_sidebar) and str(info_text_sidebar).strip() != '':
                 st.write(f"**Informações:**")
                 st.markdown(info_text_sidebar)

        else:
            st.info("Clique em um marcador no mapa para ver os detalhes aqui.")


    # --- Filtragem ---
    df_filtrado = pd.DataFrame()
    if not st.session_state.load_error and not st.session_state.df.empty:
        df_filtrado = st.session_state.df
        if 'Nome' in st.session_state.df.columns and search_query:
            df_filtrado = st.session_state.df[
                st.session_state.df["Nome"].str.lower().str.contains(search_query, na=False, regex=False)
            ]
            if df_filtrado.empty:
                st.warning(f"Nenhuma unidade encontrada contendo '{search_query}' no nome.")
        elif search_query:
             st.warning("A coluna 'Nome' não foi encontrada nos dados, a busca não pôde ser aplicada.")
             df_filtrado = pd.DataFrame()


    # --- Exibição do Mapa ---
    if not st.session_state.load_error and not df_filtrado.empty:
        geojson_to_map = st.session_state.geojson_data if st.session_state.geojson_data is not None else {"type": "FeatureCollection", "features": []}
        m = criar_mapa(df_filtrado, geojson_to_map)

        map_output = st_folium(m, width='100%', height=600, key="folium_map", returned_objects=['last_object_clicked'])

        # --- Lógica para Capturar Clique e Atualizar Sidebar ---
        if map_output and map_output.get('last_object_clicked'):
            clicked_obj = map_output['last_object_clicked']

            if 'lat' in clicked_obj and 'lng' in clicked_obj:
                clicked_lat = clicked_obj['lat']
                clicked_lon = clicked_obj['lng']

                found_row = None
                for index, row in df_filtrado.iterrows():
                    if 'lat' in row and 'lon' in row and pd.notna(row['lat']) and pd.notna(row['lon']) and np.isclose(row['lat'], clicked_lat, atol=1e-6) and np.isclose(row['lon'], clicked_lon, atol=1e-6):
                        found_row = row
                        break

                if found_row is not None:
                    st.session_state.selected_marker_info = found_row.to_dict()
                else:
                    # Limpa a sidebar se o clique for em uma feição do GeoJSON ou área sem marcador
                    st.session_state.selected_marker_info = None

    elif st.session_state.load_error:
        pass

    elif not st.session_state.df.empty and df_filtrado.empty:
        if not search_query:
             st.info("Nenhuma unidade produtiva encontrada nos dados carregados após validação.")

    elif st.session_state.df.empty and not st.session_state.load_error:
        st.info("Nenhuma unidade produtiva encontrada nos dados carregados.")


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
