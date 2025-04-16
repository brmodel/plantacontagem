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

# Template para estilização HTML do Popup com funcionalidade de colapsar
POPUP_TEMPLATE = """
<div style="font-family: Arial; font-size: 12px; min-width: 200px;">
    <h6 style="margin: 0 0 5px 0;"><b>{0}</b></h6>
    <p style="margin: 2px 0;"><b>Tipo:</b> {1}</p>
    <p style="margin: 2px 0;"><b>Regional:</b> {2}</p>
    <div class="texto-completo" id="texto-completo-{3}" style="display: none;">
        {7}
    </div>
    <button class="leia-mais-btn" onclick="toggleTexto('texto-completo-{3}', this)">Saiba Mais</button>
</div>
<script>
function toggleTexto(idElemento, botao) {{
    var elemento = document.getElementById(idElemento);
    if (elemento.style.display === "none") {{
        elemento.style.display = "block";
        botao.textContent = "Mostrar Menos";
    }} else {{
        elemento.style.display = "none";
        botao.textContent = "Saiba Mais";
    }}
}}
</script>
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
    font-size: 12px;
}}
.leia-mais-btn:hover {{
    text-decoration: underline;
}}
</style>
"""

# Carregar Database e GeoJSON em paralelo
@st.cache_data(ttl=600)
def load_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/export?format=csv&gid=1832051074"
        data = pd.read_csv(url, usecols=range(7))
        clean_data = data.dropna(subset=['Nome', 'lon', 'lat', 'Tipo', 'Regional', 'Numeral', 'Info']).copy()
        clean_data['Numeral'] = clean_data['Numeral'].astype(int)
        return clean_data
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_geojson():
    try:
        response = requests.get(GEOJSON_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {e}")
        return {"type": "FeatureCollection", "features": []}

# Criação do Mapa
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
    for region in sorted(regions, key=lambda x: x['id']):
        color = MAPEAMENTO_CORES.get(region['id'], "#fddaec")
        items_legenda.append(f"""
            <div style="display: flex; align-items: center; margin: 2px 0;">
                <div style="background: {color}; width: 20px; height: 20px; margin-right: 5px;"></div>
                <span>{region['name']}</span>
            </div>
        """)

    return folium.Element(f"""
        <div style="
            position: fixed;
            bottom: 50px;
            right: 20px;
            z-index: 1000;
            background: white;
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
    m = folium.Map(location=[-19.89323, -43.97145],
                    tiles="OpenStreetMap",
                    zoom_start=12.49,
                    control_scale=True)

    # Adiciona GEOJson com as Regionais de Contagem
    folium.GeoJson(
        geojson_data,
        name='Regionais',
        style_function=lambda x: {
            "fillColor": MAPEAMENTO_CORES.get(x['properties'].get('id'), "#fddaec"),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.3,
            "dashArray": "5,5"
        },
        tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
        interactive=True,
        control=True
    ).add_to(m)

    # Criar Unidades Produtivas como marcadores no mapa
    for index, row in data.iterrows():
        icon_url = ICONES_URL.get(row["Numeral"], ICONE_PADRAO)
        icon = folium.CustomIcon(icon_url, icon_size=(32, 32), icon_anchor=(16, 16))

        # Suponha que você tenha uma coluna 'Info' com o texto longo
        texto_completo = row.get('Info', 'Sem descrição detalhada.')
        marker_id = f"marker-{index}" # Cria um ID único para cada marcador

        popup_html = POPUP_TEMPLATE.format(
            row['Nome'],
            row['Tipo'],
            row['Regional'],
            marker_id, # Passa o ID para o template
            texto_completo
        )
        popup = folium.Popup(popup_html, max_width=300) # Ajuste o max_width conforme necessário

        Marker(
            location=[row["lat"], row["lon"]],
            popup=popup,
            icon=icon,
            tooltip=TOOLTIP_TEMPLATE.format(row['Nome'])
        ).add_to(m)

    # Adicionar controles ao mapa e legendas
    LocateControl().add_to(m)
    folium.LayerControl().add_to(m)
    legenda = criar_legenda(geojson_data)
    m.get_root().html.add_child(legenda)

    return m

# Inicialização do aplicativo e design de página
def main():
    # Carrega os dados e o GeoJSON uma única vez por sessão
    if 'data_loaded' not in st.session_state:
        st.session_state.df = load_data()
        st.session_state.geojson_data = load_geojson()
        st.session_state.data_loaded = True

    st.logo(LOGO_PMC, size="large", link="https://portal.contagem.mg.gov.br/")
    st.title(APP_TITULO)
    st.header(APP_SUBTITULO)
    search_query = st.text_input("Pesquisar por Unidades Produtivas:", "").strip().lower()

    # Filtragem da database pelo campo nome das UPs
    df_filtrado = st.session_state.df
    if search_query:
        df_filtrado = st.session_state.df[st.session_state.df["Nome"].str.lower().str.contains(search_query, regex=False)]
        if df_filtrado.empty:
            st.warning("Nenhuma unidade encontrada com esse nome")

    # Visualização do mapa
    if not st.session_state.df.empty:
        m = criar_mapa(df_filtrado, st.session_state.geojson_data)
        st_folium(m, width=1400, height=700)
    else:
        st.warning("Nenhum dado disponível para exibir")

    st.caption(APP_DESC)
    for url in BANNER_PMC:
        st.image(url, use_container_width=True)

if __name__ == "__main__":
    main()
