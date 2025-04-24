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

# Dicionário de Ícones por número (presumivelmente da coluna 'Numeral')
ICONES = {
    1: "leaf_green.png", 2: "leaf_blue.png", 3: "leaf_orange.png", 4: "leaf_purple.png",
}
# Mapeamento de Cores para as regionais (baseado no 'id' do GeoJSON)
MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5", 4: "#decbe4",
    5: "#fed9a6", 6: "#ffffcc", 7: "#e5d8bd"
}
BANNER_PMC_BASE = ["ilustracao_pmc.png", "banner_pmc.png"]
LOGO_PMC = "https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"

# --- URLs e Rótulos Pré-calculados ---
ICONES_URL = {k: ICONES_URL_BASE + v for k, v in ICONES.items()}
ICONE_PADRAO = ICONES_URL_BASE + "leaf_green.png" # Ícone padrão caso Numeral não mapeado
BANNER_PMC = [ICONES_URL_BASE + img for img in BANNER_PMC_BASE]

ICONE_LEGENDA = {
    1: "Comunitária",
    2: "Institucional",
    3: "Comunitária/Institucional",
    4: "Feira da Cidade",
}

# --- Templates HTML ---
POPUP_TEMPLATE_BASE = """
<div style="
    font-family: Arial, sans-serif; font-size: 12px;
    width: auto; max-width: min(90vw, 466px); min-width: 200px;
    word-break: break-word; box-sizing: border-box; padding: 8px;
">
    <h6 style="margin: 0 0 8px 0; word-break: break-word; font-size: 14px;"><b>{}</b></h6>
    <p style="margin: 4px 0;"><b>Tipo:</b> {}</p>
    <p style="margin: 4px 0;"><b>Regional:</b> {}</p>
    {} </div>
"""

TOOLTIP_TEMPLATE = """
<div style="font-family: Arial, sans-serif; font-size: 12px">
    <p><b>Unidade Produtiva:<br>{}</b></p>
</div>
"""

# --- Funções de Carregamento de Dados ---
@st.cache_data(ttl=600)
def load_data():
    """Carrega e pré-processa os dados da planilha Google Sheets."""
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
    try:
        # Carrega apenas as primeiras 8 colunas para otimizar
        data = pd.read_csv(url, usecols=range(8))

        # Conversões e tratamento de erros
        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')

        # Remove linhas sem coordenadas ou numeral (essenciais para o mapa)
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True)

        # Converte Numeral para Int64 (inteiro que aceita NaN, embora já tenhamos dropado NaNs aqui)
        data['Numeral'] = data['Numeral'].astype('Int64')

        # Garante que colunas de texto sejam strings (evita problemas com pd.NA)
        for col in ['Nome', 'Tipo', 'Regional', 'Info', 'Instagram']:
             if col in data.columns:
                 data[col] = data[col].astype(str).replace('nan', '', regex=False).replace('<NA>', '', regex=False)


        return data
    except pd.errors.EmptyDataError:
        st.error("Erro: A planilha parece estar vazia ou sem cabeçalhos.")
        return pd.DataFrame()
    except ValueError as e:
        st.error(f"Erro ao processar colunas: {e}. Verifique a estrutura e nomes das colunas na planilha.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    """Carrega os dados GeoJSON das regionais de Contagem."""
    default_geojson = {"type": "FeatureCollection", "features": []}
    try:
        response = requests.get(GEOJSON_URL, timeout=20) # Aumentado timeout
        response.raise_for_status() # Verifica erros HTTP
        geojson_data = response.json()
        # Validação básica da estrutura
        if not isinstance(geojson_data, dict) or "features" not in geojson_data:
            st.warning("Estrutura do GeoJSON inválida recebida da URL.")
            return default_geojson
        return geojson_data
    except requests.exceptions.Timeout:
        st.error(f"Erro ao carregar GeoJSON: Tempo limite excedido ({GEOJSON_URL})")
        return default_geojson
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de rede ao carregar GeoJSON: {e}")
        return default_geojson
    except ValueError as e: # Erro na decodificação JSON
        st.error(f"Erro ao decodificar GeoJSON: {e}")
        return default_geojson
    except Exception as e:
        st.error(f"Erro inesperado ao carregar GeoJSON: {e}")
        return default_geojson

# --- Funções de Criação do Mapa e Legenda ---

def criar_legenda(geojson_data):
    """Cria legendas HTML para Regionais (cor) e Tipos de Unidade (ícones)."""
    # --- Parte 1: Legenda das Regionais (Cores) ---
    regions = []
    if geojson_data and 'features' in geojson_data:
        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {})
            regions.append({
                'id': props.get('id'),
                'name': props.get('Name')
            })

    items_legenda_regional = []
    for region in sorted(regions, key=lambda x: x.get('id', float('inf'))):
        color = MAPEAMENTO_CORES.get(region.get('id'), "#CCCCCC") # Cor fallback cinza
        region_name = region.get('name', 'N/A')
        if region_name and color: # Só adiciona se tiver nome e cor
            items_legenda_regional.append(f"""
                <div style="display: flex; align-items: center; margin: 2px 0;">
                    <div style="background: {color}; width: 20px; height: 20px; margin-right: 5px; border: 1px solid #ccc;"></div>
                    <span>{region_name}</span>
                </div>
            """)
    html_regional = f"""
        <div style="font-weight: bold; margin-bottom: 5px;">Regionais</div>
        {"".join(items_legenda_regional)}
    """ if items_legenda_regional else ""

    # --- Parte 2: Legenda dos Ícones (Tipos de Unidade) ---
    items_legenda_icones = []
    for key, icon_url in sorted(ICONES_URL.items()):
        # Pega o rótulo do dicionário global ICONE_LEGENDA
        legenda = ICONE_LEGENDA.get(key, f"Tipo {key}") # Fallback caso não haja rótulo
        items_legenda_icones.append(f"""
             <div style="display: flex; align-items: center; margin: 2px 0;">
                 <img src="{icon_url}" alt="{legenda}" title="{legenda}" style="width: 20px; height: 20px; margin-right: 5px; object-fit: contain;">
                 <span>{legenda}</span>
             </div>
         """)
    # Adiciona título para a seção de ícones
    html_icones = f"""
        <div style="font-weight: bold; margin-top: 10px; margin-bottom: 5px;">Tipos de Unidade</div>
        {"".join(items_legenda_icones)}
     """ if items_legenda_icones else "" # Só adiciona se houver ícones

    # --- Parte 3: Montagem Final da Legenda ---
    # Só retorna a legenda se houver conteúdo (regional ou ícones)
    if html_regional or html_icones:
        return folium.Element(f"""
            <div style="
                position: fixed; bottom: 50px; right: 20px; z-index: 1000;
                background: rgba(255, 255, 255, 0.9); padding: 10px; border-radius: 5px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-family: Arial, sans-serif; font-size: 12px;
                max-width: 180px; max-height: 300px; overflow-y: auto;
            ">
                {html_regional}
                {html_icones}
            </div>
        """)
    else:
        return None # Retorna None se não houver nada para mostrar na legenda

def criar_mapa(data, geojson_data):
    m = folium.Map(location=[-19.8888, -44.0535], tiles="cartodbpositron",
                   zoom_start=12, control_scale=True)

    # Adiciona camada GeoJSON das regionais
    if geojson_data and geojson_data.get("features"):
        folium.GeoJson(
            geojson_data, name='Regionais',
            style_function=lambda x: {
                "fillColor": MAPEAMENTO_CORES.get(x['properties'].get('id'), "#CCCCCC"), # Cor fallback
                "color": "#555555", "weight": 1, "fillOpacity": 0.35, # Aumenta opacidade
            },
            tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
            highlight_function=lambda x: {"weight": 2.5, "fillOpacity": 0.6, "color": "black"}, # Melhora highlight
            interactive=True, control=True, show=True
        ).add_to(m)

    # Adiciona Marcadores das Unidades Produtivas
    if isinstance(data, pd.DataFrame) and not data.empty:
        # Cria/Atualiza o dicionário de lookup no estado da sessão para performance no clique
        coord_precision = 6
        try:
            # Garante que lat/lon são numéricos antes de arredondar/usar
            valid_coords = data[['lat', 'lon']].apply(pd.to_numeric, errors='coerce').dropna()
            rounded_coords = list(zip(np.round(valid_coords['lat'], coord_precision),
                                      np.round(valid_coords['lon'], coord_precision)))
            # Alinha os dados (como dicionário) com as coordenadas válidas
            valid_data_dict = data.loc[valid_coords.index].to_dict('records')
            st.session_state.marker_lookup = dict(zip(rounded_coords, valid_data_dict))
        except Exception as e:
             st.warning(f"Erro ao criar lookup de marcadores: {e}. Seleção por clique pode falhar.")
             st.session_state.marker_lookup = {}

        # Busca no DataFrame filtrado para criar marcadores
        for index, row in data.iterrows():
            # Pula se lat/lon não for válido (embora dropna deva ter cuidado disso)
            if pd.isna(row["lat"]) or pd.isna(row["lon"]):
                 continue

            lat, lon = row["lat"], row["lon"]
            icon_num = row["Numeral"] # Já garantido ser Int64 ou similar

            # Define o ícone baseado no 'Numeral'
            try:
                # Tenta pegar URL do dicionário, usa padrão se falhar
                icon_url = ICONES_URL.get(int(icon_num), ICONE_PADRAO)
            except (ValueError, TypeError):
                icon_url = ICONE_PADRAO # Fallback para ícone padrão

            try:
                # Cria ícone customizado
                icon = folium.CustomIcon(icon_url, icon_size=(30, 30), icon_anchor=(15, 15), popup_anchor=(0, -10))
            except Exception as e:
                # Fallback para ícone Folium padrão se CustomIcon falhar (URL inválida, etc)
                st.warning(f"Erro ao carregar ícone {icon_url} para {row.get('Nome', 'N/I')}: {e}. Usando ícone padrão.")
                icon = folium.Icon(color="green", prefix='fa', icon="leaf")

            # --- Construção do HTML do Popup (SEM 'Info') ---
            popup_parts = [] # Lista para partes condicionais do popup

            # Adiciona link do Instagram se existir
            instagram_link = row.get('Instagram', '').strip() # Pega como string e remove espaços
            if instagram_link: # Verifica se não está vazio
                 link_ig_safe = instagram_link
                 # Garante que o link tenha protocolo
                 if not link_ig_safe.startswith(('http://', 'https://')):
                      link_ig_safe = 'https://' + link_ig_safe
                 popup_parts.append(f"""
                    <p style='margin: 4px 0;'>
                        <b>Instagram:</b> <a href='{link_ig_safe}' target='_blank' rel='noopener noreferrer'>{instagram_link}</a>
                    </p>
                 """)

            # Monta o conteúdo do popup usando o template base
            popup_content = POPUP_TEMPLATE_BASE.format(
                row.get('Nome', 'Nome não informado'),
                row.get('Tipo', 'Tipo não informado'),
                row.get('Regional', 'Regional não informada'),
                "".join(popup_parts) # Adiciona partes extras (Instagram)
            )
            popup = folium.Popup(popup_content, max_width=450) # Ajusta max_width

            # Cria o Marcador
            Marker(
                location=[lat, lon],
                popup=popup, # Popup agora sem a seção 'Info'
                icon=icon,
                tooltip=TOOLTIP_TEMPLATE.format(row.get('Nome', 'N/I')) # Tooltip simples
            ).add_to(m)

    # Adiciona Controles ao Mapa
    LocateControl(strings={"title": "Mostrar minha localização", "popup": "Você está aqui"}).add_to(m)
    folium.LayerControl(position='topright').add_to(m) # Controle de camadas

    # Adiciona a Legenda HTML ao mapa (se houver conteúdo na legenda)
    legenda = criar_legenda(geojson_data)
    if legenda:
        m.get_root().html.add_child(legenda)

    return m

# --- App Principal Streamlit ---
def main():
    """Função principal que roda o aplicativo Streamlit."""
    st.set_page_config(page_title=APP_TITULO, layout="wide", initial_sidebar_state="expanded")

    # --- Inicialização do Estado da Sessão ---
    # Guarda dados carregados, seleção, busca, etc., entre re-execuções
    if 'selected_marker_info' not in st.session_state:
        st.session_state.selected_marker_info = None # Info do marcador clicado para a sidebar
    if 'search_input_value' not in st.session_state:
        st.session_state.search_input_value = '' # Valor atual da caixa de busca
    if 'marker_lookup' not in st.session_state:
        st.session_state.marker_lookup = {} # Dicionário para buscar marcador por coordenada
    if 'data_loaded' not in st.session_state:
         st.session_state.data_loaded = False # Flag para controlar carregamento inicial
         st.session_state.load_error = False # Flag para erro no carregamento de dados
         st.session_state.df = pd.DataFrame() # DataFrame principal
         st.session_state.geojson_data = None # Dados GeoJSON

    # --- Carregamento de Dados Inicial ---
    # Executa apenas na primeira vez ou se o cache expirar
    if not st.session_state.data_loaded:
        with st.spinner("Carregando dados das unidades..."):
            loaded_df = load_data()
            if not loaded_df.empty:
                st.session_state.df = loaded_df
            else:
                st.session_state.load_error = True # Marca erro se o df vier vazio
        with st.spinner("Carregando mapa das regionais..."):
            geojson = load_geojson()
            # Guarda mesmo se vazio/inválido, para não tentar carregar de novo
            st.session_state.geojson_data = geojson
        st.session_state.data_loaded = True # Marca que o carregamento foi feito

    # --- Layout Principal (Título, Logo, Busca) ---
    col1, col2 = st.columns([3, 1]) # Divide em 2 colunas
    with col1:
        st.title(APP_TITULO)
        st.header(APP_SUBTITULO)
    with col2:
        st.image(LOGO_PMC, width=150) # Exibe logo com tamanho controlado

        # Caixa de busca com callback para limpar seleção ao buscar
        def clear_selection_on_search():
             st.session_state.selected_marker_info = None # Limpa info na sidebar
             # Atualiza o valor da busca no estado
             st.session_state.search_input_value = st.session_state.search_input_widget_key

        search_query = st.text_input(
            "Pesquisar por Nome:",
            key="search_input_widget_key", # Chave única para o widget
            on_change=clear_selection_on_search, # Função chamada ao mudar o texto
            value=st.session_state.search_input_value # Controla o valor pelo estado
        ).strip().lower() # Processa o valor da busca

    # --- Sidebar (Exibe detalhes do marcador selecionado) ---
    with st.sidebar:
        st.title("Detalhes da Unidade")
        # Verifica se há informação selecionada no estado da sessão
        selected_info = st.session_state.selected_marker_info
        if selected_info:
            # Exibe informações básicas
            st.header(selected_info.get('Nome', 'Nome não informado'))
            st.write(f"**Tipo:** {selected_info.get('Tipo', 'N/I')}")
            st.write(f"**Regional:** {selected_info.get('Regional', 'N/I')}")

            # Exibe link do Instagram se houver
            redes = selected_info.get('Instagram', '').strip()
            if redes:
                 link_ig = redes
                 if not link_ig.startswith(('http://', 'https://')):
                      link_ig = 'https://' + link_ig
                 st.write(f"**Instagram:**")
                 st.markdown(f"[{redes}]({link_ig})") # Usa markdown para link clicável

            # Exibe a seção 'Info' (que foi removida do popup)
            info_text_sidebar = selected_info.get('Info', '').strip()
            if info_text_sidebar:
                st.write(f"**Informações:**")
                st.markdown(info_text_sidebar) # Usa markdown para formatar texto se necessário
        else:
            # Mensagem padrão se nada estiver selecionado
            st.info("Clique em um marcador no mapa para ver os detalhes aqui.")

    # --- Filtragem dos Dados baseado na Busca ---
    df_filtrado = pd.DataFrame() # Inicializa DataFrame vazio
    # Procede apenas se os dados foram carregados sem erro
    if not st.session_state.load_error and not st.session_state.df.empty:
        df_original = st.session_state.df
        # Aplica filtro de busca se houver query e a coluna 'Nome' existir
        if search_query and 'Nome' in df_original.columns:
            try:
                df_filtrado = df_original[
                    # Busca case-insensitive que contém a query
                    df_original["Nome"].str.contains(search_query, case=False, na=False, regex=False)
                ]
                if df_filtrado.empty:
                    # Aviso se o filtro não retornar resultados
                    st.warning(f"Nenhuma unidade encontrada contendo '{search_query}' no nome.")
            except Exception as e:
                st.error(f"Erro ao aplicar filtro de busca: {e}")
                df_filtrado = df_original # Em caso de erro no filtro, mostra todos
        elif search_query:
             # Aviso se a busca foi feita mas a coluna 'Nome' não existe
             st.warning("Coluna 'Nome' não encontrada nos dados. Não é possível filtrar.")
             df_filtrado = pd.DataFrame() # Mostra mapa vazio
        else:
            # Se não houver busca, usa todos os dados carregados
            df_filtrado = df_original

    # --- Exibição do Mapa e Processamento de Interação ---
    # Só exibe o mapa se houver dados filtrados para mostrar
    if not df_filtrado.empty:
        # Pega o GeoJSON do estado (pode ser None ou inválido, criar_mapa lida com isso)
        geojson_to_map = st.session_state.geojson_data

        # Cria o mapa com os dados JÁ FILTRADOS
        # A função criar_mapa também atualiza o st.session_state.marker_lookup
        m = criar_mapa(df_filtrado, geojson_to_map)

        # Renderiza o mapa usando st_folium e captura interações
        map_output = st_folium(
            m,
            width='100%',
            height=600,
            key="folium_map_key", # Chave única para o componente do mapa
            returned_objects=['last_object_clicked'] # Pede para retornar info do último clique
        )

        # --- Lógica de Atualização da Sidebar Pós-Clique ---
        # Verifica se houve um clique na última interação que causou este rerun
        if map_output and map_output.get('last_object_clicked'):
            clicked_obj = map_output['last_object_clicked']

            # Verifica se o clique foi em um marcador (tem lat/lng)
            if clicked_obj and 'lat' in clicked_obj and 'lng' in clicked_obj:
                clicked_lat = clicked_obj['lat']
                clicked_lon = clicked_obj['lng']
                coord_precision = 6 # Mesma precisão usada ao criar o lookup
                clicked_key = (round(clicked_lat, coord_precision), round(clicked_lon, coord_precision))

                # Procura no dicionário de lookup atualizado
                found_info = st.session_state.marker_lookup.get(clicked_key)

                # Compara com o estado atual para evitar reruns desnecessários
                if found_info != st.session_state.selected_marker_info:
                    st.session_state.selected_marker_info = found_info # Atualiza estado
                    st.rerun() # Força rerun para atualizar a sidebar "imediatamente"
            else:
                 # Se clicou em algo sem lat/lng (ex: GeoJSON) ou fora de tudo, limpa seleção
                 if st.session_state.selected_marker_info is not None:
                     st.session_state.selected_marker_info = None
                     st.rerun() # Força rerun para limpar a sidebar

    # --- Mensagens Alternativas (Erro, Sem Dados, etc.) ---
    elif st.session_state.load_error:
        st.error("Falha crítica ao carregar dados das unidades. Mapa não pode ser exibido.")
    elif not st.session_state.df.empty and df_filtrado.empty and search_query:
        # Caso onde os dados existem, mas a busca não retornou nada (warning já exibido)
        pass
    else:
        # Caso geral onde não há dados para exibir (ou erro inicial não crítico)
        if not search_query: # Só mostra se não for resultado de busca vazia
            st.info("Não há unidades produtivas para exibir no mapa.")

    # --- Rodapé ---
    st.markdown("---")
    st.caption(APP_DESC)
    # Exibe banners lado a lado se houver mais de um
    if len(BANNER_PMC) > 1:
        cols_banner = st.columns(len(BANNER_PMC))
        for i, url in enumerate(BANNER_PMC):
            with cols_banner[i]:
                st.image(url, use_container_width=True)
    elif BANNER_PMC: # Exibe único banner se houver apenas um
        st.image(BANNER_PMC[0], use_container_width=True)

# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    main()
