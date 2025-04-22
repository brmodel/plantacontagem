# -*- coding: utf-8 -*- # Adicionado para garantir codificação correta
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl
# Removido: import logging
import numpy as np # Para comparações de ponto flutuante seguras

# Removido: Configuração básica de logging
# logging.basicConfig(level=logging.INFO)

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
# !!! CORRIGIDO: O nome da coluna é "Instagram" na planilha.
essential_cols = ['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral', 'Info', 'Instagram'] # Corrigido para "Instagram"


# --- URLs Pré-calculadas ---
ICONES_URL = {k: ICONES_URL_BASE + v for k, v in ICONES.items()}
ICONE_PADRAO = ICONES_URL_BASE + "leaf_green.png"
BANNER_PMC = [ICONES_URL_BASE + img for img in BANNER_PMC_BASE]

# --- Templates HTML (Simplificados) ---
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
    # Use a URL de exportação CSV correta para o pandas ler o conteúdo raw
    url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
    try:
        # Usando range(8) conforme solicitado. Assumimos que as colunas essenciais
        # são as primeiras 8 colunas por índice (0 a 7) no CSV e que o pandas
        # atribuirá corretamente os nomes do cabeçalho a essas colunas.
        # Este método DEPENDE da ordem das colunas na planilha.
        data = pd.read_csv(url, usecols=range(8))

        # Após carregar com range(8), o DataFrame 'data' deve ter os nomes do cabeçalho do CSV.
        # Precisamos garantir que os nomes essenciais existem (agora incluindo "Instagram").

        # Continuar com a limpeza dos dados
        # Remove linhas onde QUALQUER coluna essencial (pelos nomes carregados, incluindo "Instagram") está faltando
        initial_rows = data.shape[0]
        # !!! Importante: Aqui usamos 'Instagram' conforme o nome real da planilha !!!
        data.dropna(subset=essential_cols, inplace=True) # Usa a lista essential_cols corrigida
        rows_after_essential_dropna = data.shape[0]
        if initial_rows > rows_after_essential_dropna:
             st.warning(f"{initial_rows - rows_after_essential_dropna} linhas removidas por falta de dados em colunas essenciais.")


        # Convertendo Numeral, lat, lon para numérico, tratando erros como NaN
        data['Numeral'] = pd.to_numeric(data['Numeral'], errors='coerce')
        data['lat'] = pd.to_numeric(data['lat'], errors='coerce')
        data['lon'] = pd.to_numeric(data['lon'], errors='coerce')

        # Esta dropna garante que as colunas CRUCIAIS para o mapa (lat, lon, Numeral) estejam preenchidas APÓS a conversão numérica
        rows_before_mapping_dropna = data.shape[0]
        # !!! Importante: Aqui a dropna ainda foca nas colunas de mapeamento, mantendo Numeral, lat, lon
        data.dropna(subset=['Numeral', 'lat', 'lon'], inplace=True)
        rows_after_mapping_dropna = data.shape[0]
        if rows_before_mapping_dropna > rows_after_mapping_dropna:
            st.warning(f"{rows_before_mapping_dropna - rows_after_mapping_dropna} linhas removidas por valores inválidos ou ausentes em Numeral, lat ou lon APÓS conversão numérica.")


        # Convertendo Numeral para tipo inteiro que aceita NaN (Int64)
        # Isso deve ser feito APÓS as dropna que garantem que Numeral não é NaN.
        data['Numeral'] = data['Numeral'].astype('Int64')


        # Adicionar um ID único baseado no índice do DataFrame *final* (após dropna)
        data['marker_id'] = data.index.map(lambda i: f'up-{i}')


        return data # Retorna o DataFrame processado
    except pd.errors.EmptyDataError:
        st.error("O arquivo CSV da planilha parece estar vazio ou não contém cabeçalhos.")
        return pd.DataFrame()
    except ValueError as e:
        # Este pode ser o erro original com usecols=range(8), erro de conversão numérica,
        # OU um erro se um dos nomes de coluna em essential_cols (como "Instagram") não existir
        # no DataFrame carregado por range(8).
        st.error(f"Erro ao processar colunas ou dados da planilha: {e}. Verifique a estrutura do CSV, os tipos de dados, E SE OS NOMES DAS COLUNAS EM essential_cols correspondem ao cabeçalho das primeiras 8 colunas do CSV.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro inesperado ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    # Removido: logging.info(f"Tentando carregar GeoJSON de: {GEOJSON_URL}")
    default_geojson = {"type": "FeatureCollection", "features": []}
    try:
        response = requests.get(GEOJSON_URL, timeout=15)
        response.raise_for_status()
        geojson_data = response.json()
        if not isinstance(geojson_data, dict) or "features" not in geojson_data:
            st.warning("Estrutura do GeoJSON inválida.")
            return default_geojson
        # Removido: logging.info(f"GeoJSON carregado com {len(geojson_data.get('features', []))} features.")
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
def criar_mapa(data, geojson_data):
    # Removido: logging.info("Iniciando criação do mapa Folium.")
    # Coordenadas centrais para Contagem, MG
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
        # Removido: logging.info("Camada GeoJSON adicionada ao mapa.")
    else:
        # Não exibe warning se GeoJSON não carregar aqui, já é mostrado na função de carregamento
        pass

    marker_count = 0
    # Adicionando uma verificação para garantir que 'data' é um DataFrame antes de iterar
    if isinstance(data, pd.DataFrame) and not data.empty:
        for index, row in data.iterrows():
            # Verifica se as colunas lat e lon existem e são válidas na linha
            # Se as dropna anteriores funcionaram, elas devem existir e ser numéricas.
            if 'lat' not in row or 'lon' not in row or pd.isna(row['lat']) or pd.isna(row['lon']) or not isinstance(row['lat'], (int, float)) or not isinstance(row['lon'], (int, float)):
                 st.warning(f"Colunas 'lat' ou 'lon' ausentes, inválidas ou vazias na linha (Índice: {index}). Pulando marcador.")
                 continue

            lat, lon = row["lat"], row["lon"]

            # Verifica se a coluna 'Numeral' existe e é válida na linha
            if 'Numeral' not in row or pd.isna(row['Numeral']):
                 st.warning(f"Coluna 'Numeral' ausente ou vazia na linha (Índice: {index}). Usando ícone padrão.")
                 icon_url = ICONE_PADRAO
            else:
                icon_num = row["Numeral"]
                # Garante que icon_num é um inteiro válido antes de usá-lo como chave.
                # A dropna e astype('Int64') devem garantir isso.
                # Acesso seguro ao dicionário ICONES_URL
                try:
                    icon_url = ICONES_URL.get(int(icon_num), ICONE_PADRAO)
                except (ValueError, TypeError): # Em caso de Numeral não ser conversível para int
                    st.warning(f"Valor de 'Numeral' inválido '{icon_num}' na linha (Índice: {index}). Usando ícone padrão.")
                    icon_url = ICONE_PADRAO


            try:
                icon = folium.CustomIcon(icon_url, icon_size=(30, 30), icon_anchor=(15, 15), popup_anchor=(0, -10))
            except Exception as e:
                st.error(f"Erro ao carregar ícone {icon_url} para {row.get('Nome', 'N/I')}: {e}. Usando ícone padrão.")
                # Fallback para Icon padrão do Folium se o CustomIcon falhar
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
                # Não passamos marker_id diretamente para o Marker, st_folium cuida disso no retorno
            ).add_to(m)
            marker_count += 1

    # Removido: logging.info(f"{marker_count} marcadores adicionados ao mapa.")

    LocateControl(strings={"title": "Mostrar minha localização", "popup": "Você está aqui"}).add_to(m)
    folium.LayerControl(position='topright').add_to(m)
    if geojson_data and geojson_data.get("features"):
        legenda = criar_legenda(geojson_data)
        m.get_root().html.add_child(legenda)
        # Removido: logging.info("Legenda das regionais adicionada ao mapa.")

    # Removido: logging.info("Criação do mapa Folium concluída.")
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

    # --- Carregamento de Dados Inicial (Apenas na primeira execução ou mudança de cache) ---
    # Usamos st.session_state.data_loaded para evitar recarregar dados toda vez
    if 'data_loaded' not in st.session_state:
        st.session_state.load_error = False
        st.session_state.df = pd.DataFrame() # Inicializa como DataFrame vazio
        st.session_state.geojson_data = None # Inicializa como None

        with st.spinner("Carregando dados das unidades..."):
            # Chama a função de carregamento
            loaded_df = load_data()
            if not loaded_df.empty:
                st.session_state.df = loaded_df
            else:
                st.session_state.load_error = True # Marca erro se o DF estiver vazio

        with st.spinner("Carregando mapa das regionais..."):
            geojson = load_geojson()
            if geojson and geojson.get("features"):
                st.session_state.geojson_data = geojson
            else:
                # Não marca como erro fatal se GeoJSON falhar, o mapa só não terá as regionais
                st.warning("Não foi possível carregar os dados das regionais para o mapa.") # Mantido o st.warning

        st.session_state.data_loaded = True # Marca que o carregamento inicial foi tentado

    # --- Layout Principal (Colunas) ---
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(APP_TITULO)
        st.header(APP_SUBTITULO)
    with col2:
        st.markdown(f"[![Logo PMC]({LOGO_PMC})]({LOGO_PMC})", unsafe_allow_html=True)
        # A chave "search_input_widget" mantém o estado do input.
        search_query = st.text_input("Pesquisar por Nome:", key="search_input_widget",
                                     value=st.session_state.search_input_value).strip().lower()

        # Só atualiza o estado da busca se o valor do widget mudou
        if search_query != st.session_state.search_input_value:
            st.session_state.search_input_value = search_query
            # Opcional: Se a busca mudar, talvez queira limpar a info da sidebar
            # st.session_state.selected_marker_info = None # Limpa se não encontrar


    # --- Lógica da Sidebar ---
    # A sidebar deve ser definida ANTES da chamada st_folium para que ela exista no primeiro rerun
    # mesmo antes de qualquer clique.
    with st.sidebar:
        st.title("Detalhes da Unidade")
        # Verifica se há informação de marcador selecionado no estado
        if st.session_state.selected_marker_info:
            info = st.session_state.selected_marker_info
            # Exibe as informações completas na sidebar
            st.header(info.get('Nome', 'Nome não informado'))
            st.write(f"**Tipo:** {info.get('Tipo', 'Tipo não informado')}")
            st.write(f"**Regional:** {info.get('Regional', 'Regional não informada')}")
            st.write(f"**Informações:**")
            # Permite Markdown simples na info da sidebar, se a coluna contiver formatação
            st.markdown(info.get('Info', 'Sem descrição detalhada.'))
            # Adiciona link para redes sociais se existir.
            # !!! Importante: Aqui usamos 'Instagram' conforme o nome real da planilha !!!
            redes = info.get('Instagram') # Corrigido para "Instagram"
            if redes and isinstance(redes, str) and redes.strip() != "":
                st.write(f"**Instagram:** [Link]({redes.strip()})") # Corrigido texto na sidebar
        else:
            st.info("Clique em um marcador no mapa para ver os detalhes aqui.")


    # --- Filtragem ---
    df_filtrado = pd.DataFrame()
    # Só aplica filtro se os dados foram carregados com sucesso
    if not st.session_state.load_error and not st.session_state.df.empty:
        df_filtrado = st.session_state.df
        if search_query:
            df_filtrado = st.session_state.df[
                st.session_state.df["Nome"].str.lower().str.contains(search_query, na=False, regex=False)
            ]
            if df_filtrado.empty:
                st.warning(f"Nenhuma unidade encontrada contendo '{search_query}' no nome.")

    # --- Exibição do Mapa ---
    # O mapa só é exibido se não houver erro crítico nos dados principais E houver dados para exibir após o filtro
    if not st.session_state.load_error and not df_filtrado.empty:
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
            # Removido: logging.info(f"Objeto clicado no mapa: {clicked_obj}")

            # Verifica se o objeto clicado tem coordenadas (marcadores e feições GeoJson pontuais/centroides)
            if 'lat' in clicked_obj and 'lng' in clicked_obj:
                clicked_lat = clicked_obj['lat']
                clicked_lon = clicked_obj['lng']
                # Removido: logging.info(f"Clique detectado em Lat: {clicked_lat}, Lon: {clicked_lon}")

                # Tenta encontrar a linha do DataFrame que corresponde a estas coordenadas
                found_row = None
                # Iteramos sobre as linhas do DataFrame *filtrado* atualmente exibido no mapa
                # para encontrar a unidade clicada pelas coordenadas.
                for index, row in df_filtrado.iterrows():
                    # Compara as coordenadas do clique com as coordenadas da linha usando tolerância
                    # Usamos um tolerance razoável para imprecisões de ponto flutuante.
                    # Verifica se 'lat' e 'lon' existem na linha antes de compará-las
                    if 'lat' in row and 'lon' in row and np.isclose(row['lat'], clicked_lat, atol=1e-6) and np.isclose(row['lon'], clicked_lon, atol=1e-6):
                        found_row = row
                        # Removido: logging.info(f"Encontrada linha correspondente (Índice: {index}) para o clique Lat/Lon.")
                        break # Encontramos a linha correspondente, saímos do loop

                if found_row is not None:
                    # Armazena as informações completas da linha encontrada no session_state
                    # O .to_dict() converte a Série Pandas (linha do DF) para um dicionário
                    st.session_state.selected_marker_info = found_row.to_dict()
                    # Removido: logging.info("Sidebar info atualizada no session_state com dados do clique.")
                    # Streamlit detecta a mudança no session_state e dispara um rerun automaticamente
                    # (Não precisamos chamar st.rerun() explicitamente aqui)
                else:
                    # Removido: logging.warning(f"Clique em Lat: {clicked_lat}, Lon: {clicked_lon} não correspondeu a nenhuma linha no DF filtrado.Sidebar não atualizada.")
                    # Limpa a sidebar se o clique não for em um marcador conhecido
                    st.session_state.selected_marker_info = None

    elif st.session_state.load_error:
        # Mensagem de erro já foi mostrada em load_data
        pass # Não exibe mapa se houver erro fatal no carregamento

    elif not st.session_state.df.empty and df_filtrado.empty:
        # Os dados originais carregaram, mas o filtro não encontrou nada
        # A mensagem de warning já foi mostrada na seção de Filtragem
        pass # Não exibe mapa se o filtro retornar vazio

    elif st.session_state.df.empty and not st.session_state.load_error:
        # Os dados carregaram, mas a planilha estava vazia desde o início
        st.info("Nenhuma unidade produtiva encontrada nos dados carregados.")
        # Não exibe mapa


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
