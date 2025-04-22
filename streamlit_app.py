import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Marker
import requests
from folium.plugins import LocateControl

# Configurações
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
APP_DESC = "Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF), em parceria com a Prefeitura Municipal de Contagem - MG"
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
ICONES = {
    1: "leaf_green.png",
    2: "leaf_orange.png",
    3: "leaf_blue.png",
    4: "leaf_purple.png",
}
MAPEAMENTO_CORES = {
    1: "#fbb4ae", 2: "#b3cde3", 3: "#ccebc5",
    4: "#decbe4", 5: "#fed9a6", 6: "#ffffcc",
    7: "#e5d8bd"
}
BANNER_PMC_BASE = [
    "ilustracao_pmc.png",
    "banner_pmc.png"
]
LOGO_PMC = "https://github.com/brmodel/plantacontagem/blob/main/images/contagem_sem_fome.png?raw=true"
GEOJSON_URL = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/data/regionais_contagem.geojson"

# Precomputed URLs
ICONES_URL = {k: ICONES_URL_BASE + v for k, v in ICONES.items()}
ICONE_PADRAO = ICONES_URL_BASE + "leaf_green.png"
BANNER_PMC = [ICONES_URL_BASE + img for img in BANNER_PMC_BASE]

# Template para estilização HTML do Tooltip
TOOLTIP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px">
    <p><b>Unidade Produtiva:<br>{}</b></p>
</div>
"""

# Template para o CONTEÚDO HTML do Popup (SEM O SCRIPT INLINE)
POPUP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px; min-width: 200px; max-width: 466px; word-break: break-word;">
    <h6 style="margin: 0 0 5px 0; word-break: break-word;"><b>{0}</b></h6>
    <p style="margin: 2px 0;"><b>Tipo:</b> {1}</p>
    <p style="margin: 2px 0;"><b>Regional:</b> {2}</p>
    <div class="texto-curto" id="texto-curto-{3}">
        {4}
    </div>
    <div class="texto-completo" id="texto-completo-{3}" style="display: none;">
        {5}
    </div>
    <button class="leia-mais-btn" onclick="toggleTexto('texto-curto-{3}', 'texto-completo-{3}', this)">Saiba Mais</button>
</div>
<style>
.texto-completo {{
    margin-top: 5px;
}}
.leia-mais-btn {{
    background: none;
    border: none;
    color: blue;
    cursor: pointer;
    padding: 0;
    font-size: 10px; /* Ajustado para melhor visibilidade */
    margin-top: 5px; /* Adiciona um pequeno espaço acima */
}}
.leia-mais-btn:hover {{
    text-decoration: underline;
}}
</style>
"""

# Definição da função JavaScript como string
TOGGLE_TEXTO_JS = """
function toggleTexto(idCurto, idCompleto, botao) {
    var elementoCurto = document.getElementById(idCurto);
    var elementoCompleto = document.getElementById(idCompleto);

    if (!elementoCurto || !elementoCompleto || !botao) {
        console.error("Elementos não encontrados para toggleTexto:", idCurto, idCompleto);
        return; // Sai se algum elemento não for encontrado
    }

    // Verifica o estado do elemento completo (mais robusto que checar só 'none')
    if (elementoCompleto.style.display === "none" || elementoCompleto.style.display === "") {
        elementoCurto.style.display = "none";
        elementoCompleto.style.display = "block";
        botao.textContent = "Mostrar Menos";
    } else {
        elementoCurto.style.display = "block"; // Ou o display original se for diferente
        elementoCompleto.style.display = "none";
        botao.textContent = "Saiba Mais";
    }
}
"""

# Carregar Database e GeoJSON em paralelo
@st.cache_data(ttl=600)
def load_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
        data = pd.read_csv(url, usecols=range(7))
        # Garante que colunas essenciais não sejam nulas
        clean_data = data.dropna(subset=['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral', 'Info']).copy()
        clean_data['Numeral'] = clean_data['Numeral'].astype(int)
        # Converte lat/lon para float explicitamente, tratando erros
        clean_data['lat'] = pd.to_numeric(clean_data['lat'], errors='coerce')
        clean_data['lon'] = pd.to_numeric(clean_data['lon'], errors='coerce')
        clean_data.dropna(subset=['lat', 'lon'], inplace=True) # Remove linhas onde lat/lon não puderam ser convertidos
        return clean_data
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    try:
        response = requests.get(GEOJSON_URL)
        response.raise_for_status() # Verifica se houve erro no request HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de rede ao carregar GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}
    except Exception as e:
        st.error(f"Erro ao processar GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}

# Criação da Legenda
def criar_legenda(geojson_data):
    """Cria legendas HTML baseadas nos dados GeoJSON"""
    regions = []
    # Verifica se geojson_data e 'features' existem e são listas
    features = geojson_data.get('features') if isinstance(geojson_data, dict) else None
    if isinstance(features, list):
        for feature in features:
            props = feature.get('properties') if isinstance(feature, dict) else {}
            if isinstance(props, dict):
                 # Garante que id e Name existam antes de adicionar
                 region_id = props.get('id')
                 region_name = props.get('Name')
                 if region_id is not None and region_name is not None:
                    regions.append({
                        'id': region_id,
                        'name': region_name
                    })

    items_legenda = []
    # Ordena por ID antes de criar os itens
    for region in sorted(regions, key=lambda x: x['id']):
        color = MAPEAMENTO_CORES.get(region['id'], "#cccccc") # Cor padrão cinza
        items_legenda.append(f"""
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="background: {color}; width: 20px; height: 20px; margin-right: 5px; border: 1px solid #ccc;"></div>
                <span>{region['name']}</span>
            </div>
        """)

    # Retorna um objeto folium.Element para ser adicionado ao mapa
    return folium.Element(f"""
        <div style="
            position: fixed;
            bottom: 50px;
            right: 20px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.9); /* Fundo levemente transparente */
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif;
            font-size: 12px;
            max-width: 150px;
            max-height: 300px; /* Limita altura máxima */
            overflow-y: auto; /* Adiciona scroll se necessário */
        ">
            <div style="font-weight: bold; margin-bottom: 5px;">Regionais</div>
            {"".join(items_legenda)}
        </div>
    """)

# Criação do Mapa
def criar_mapa(data, geojson_data):
    # Centraliza um pouco melhor em Contagem
    m = folium.Map(location=[-19.9208, -44.0535],
                   tiles="OpenStreetMap",
                   zoom_start=12, # Zoom inicial ligeiramente menor
                   control_scale=True)

    # Adiciona GEOJson com as Regionais de Contagem
    if geojson_data and geojson_data.get("features"): # Verifica se há features para desenhar
        folium.GeoJson(
            geojson_data,
            name='Regionais',
            style_function=lambda x: {
                "fillColor": MAPEAMENTO_CORES.get(x['properties'].get('id'), "#fddaec"),
                "color": "black",
                "weight": 1.5, # Linha um pouco mais grossa
                "fillOpacity": 0.35, # Opacidade ligeiramente maior
                "dashArray": "5,5"
            },
            tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
            highlight_function=lambda x: {"weight": 3, "fillOpacity": 0.5}, # Destaca ao passar o mouse
            interactive=True,
            control=True
        ).add_to(m)
    else:
        st.warning("Dados GeoJSON das regionais não puderam ser carregados ou estão vazios.")


    # Criar Unidades Produtivas como marcadores no mapa
    max_chars = 150 # Define o número máximo de caracteres a serem exibidos inicialmente
    for index, row in data.iterrows():
        # Verifica se lat e lon são válidos
        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            st.warning(f"Coordenadas inválidas para a unidade: {row.get('Nome', 'Nome não disponível')} - Índice: {index}")
            continue # Pula este marcador se as coordenadas forem inválidas

        icon_url = ICONES_URL.get(row["Numeral"], ICONE_PADRAO)
        try:
            icon = folium.CustomIcon(icon_url, icon_size=(32, 32), icon_anchor=(16, 16))
        except Exception as e:
            st.error(f"Erro ao carregar ícone {icon_url}: {e}. Usando ícone padrão.")
            icon = folium.Icon(color="green", icon="leaf") # Fallback para ícone padrão do Folium

        texto_completo = str(row.get('Info', 'Sem descrição detalhada.')) # Garante que seja string
        texto_curto = texto_completo[:max_chars] + ('...' if len(texto_completo) > max_chars else '')
        marker_id = f"marker-{index}" # Cria um ID único para cada marcador

        # Usa o POPUP_TEMPLATE SEM o script inline
        popup_html = POPUP_TEMPLATE.format(
            row['Nome'],
            row['Tipo'],
            row['Regional'],
            marker_id, # ID único passado para o HTML/JS
            texto_curto,
            texto_completo
        )
        popup = folium.Popup(popup_html, max_width=500)

        Marker(
            location=[row["lat"], row["lon"]],
            popup=popup,
            icon=icon,
            tooltip=TOOLTIP_TEMPLATE.format(row['Nome']) # Tooltip simples
        ).add_to(m)

    # --- Adiciona a função JavaScript ao <head> do mapa ---
    # Isso garante que a função toggleTexto esteja definida globalmente
    script_element = folium.Element(f"<script>{TOGGLE_TEXTO_JS}</script>")
    m.get_root().header.add_child(script_element)
    # --- Fim da Adição ---

    # Adicionar controles ao mapa e legendas
    LocateControl(strings={"title": "Mostrar minha localização", "popup": "Você está aqui"}).add_to(m) # Traduz textos
    folium.LayerControl(position='topright').add_to(m) # Move controle de camadas

    # Adiciona a legenda HTML ao corpo do mapa
    # Verifica se geojson_data existe antes de criar a legenda
    if geojson_data:
       legenda = criar_legenda(geojson_data)
       m.get_root().html.add_child(legenda) # Adiciona elemento HTML da legenda

    return m

# Inicialização do aplicativo e design de página
def main():
    st.set_page_config(page_title=APP_TITULO, layout="wide") # Usa layout largo

    # Carrega os dados e o GeoJSON uma única vez por sessão
    # Usando st.session_state para persistir os dados carregados
    if 'data_loaded' not in st.session_state:
        with st.spinner("Carregando dados das unidades..."):
            st.session_state.df = load_data()
        with st.spinner("Carregando mapa das regionais..."):
            st.session_state.geojson_data = load_geojson()
        st.session_state.data_loaded = True
        # Força recarregamento da página se o carregamento inicial falhar e o usuário tentar de novo?
        # Ou apenas mostra o erro persistente.

    # Verifica se o DataFrame foi carregado corretamente
    if st.session_state.df.empty:
        st.error("Não foi possível carregar os dados das unidades produtivas. Verifique a planilha ou a conexão.")
        st.stop() # Interrompe a execução se os dados principais falharem

    # Layout com Colunas para Título e Logo/Pesquisa
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(APP_TITULO)
        st.header(APP_SUBTITULO)
    with col2:
        st.logo(LOGO_PMC, link="https://portal.contagem.mg.gov.br/")
        search_query = st.text_input("Pesquisar Unidades por Nome:", "").strip().lower()


    # Filtragem da database pelo campo nome das UPs
    df_filtrado = st.session_state.df
    if search_query:
        # Usando contains sem regex para busca simples de substring, case-insensitive
        df_filtrado = st.session_state.df[st.session_state.df["Nome"].str.lower().str.contains(search_query, na=False, regex=False)]
        if df_filtrado.empty:
            st.warning(f"Nenhuma unidade encontrada contendo '{search_query}' no nome.")
        else:
             st.info(f"{len(df_filtrado)} unidade(s) encontrada(s) contendo '{search_query}'.")


    # Visualização do mapa
    # Verifica novamente se há dados filtrados para exibir
    if not df_filtrado.empty:
        m = criar_mapa(df_filtrado, st.session_state.geojson_data)
        # Ajusta a largura e altura para o layout 'wide'
        st_folium(m, width='100%', height=650, returned_objects=[]) # Usa largura total, ajusta altura
    elif not search_query:
         # Caso inicial sem filtro e sem dados (já tratado acima)
         st.warning("Nenhum dado de unidade produtiva disponível para exibir no mapa.")
    # Se df_filtrado está vazio por causa da pesquisa, o warning já foi mostrado acima.

    st.markdown("---") # Linha divisória
    st.caption(APP_DESC)
    # Exibe banners em colunas se houver mais de um
    if len(BANNER_PMC) > 1:
        cols_banner = st.columns(len(BANNER_PMC))
        for i, url in enumerate(BANNER_PMC):
            with cols_banner[i]:
                st.image(url, use_container_width=True)
    elif BANNER_PMC:
        st.image(BANNER_PMC[0], use_container_width=True)


if __name__ == "__main__":
    main()
