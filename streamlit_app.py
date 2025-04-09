import streamlit as st
import geopandas as gpd
import folium as fol
import folium.features as folf
from streamlit_gsheets import GSheetsConnection
import pyogrio as pyo
import requests
from streamlit_folium import st_folium
import branca

## Configurações da Página ##
st.set_page_config(layout="wide")

APP_TITLE = 'Mapeamento da Agricultura Urbana em Contagem'
APP_SUB_TITLE = 'WebApp criado para identificar as Unidades Produtivas Ativas em parceria com a Prefeitura de Contagem'

## Carregar dados do Google Sheets ##
conn = st.connection("gsheets", type=GSheetsConnection)
url = "https://docs.google.com/spreadsheets/d/16t5iUxuwnNq60yG7YoFnJw3RWnko9-YkkAIFGf6xbTM/edit?gid=1832051074#gid=1832051074"
data_ups_sujo = conn.read(spreadsheet=url, usecols=list(range(6)), worksheet="1832051074")

## Remover pontos com coordenadas vazias ##
data_ups = data_ups_sujo.dropna(subset=['Nome','lon','lat','Tipo','Regional','Numeral'])

## Carregar GeoJSON ##
geojson_url = "https://raw.githubusercontent.com/brmodel/mapeamento_agricultura_contagem/main/data/regionais_contagem.geojson"
regionais_json = requests.get(geojson_url).json()

# Criar GeoDataFrame
gdf_ups = gpd.GeoDataFrame(
    data_ups,
    geometry=gpd.points_from_xy(data_ups["lon"], data_ups["lat"])
)

## Funções para Estilo e Elementos Gráficos##
def colorir_regional(feature):
    cores = {
        1: "#fbb4ae",
        2: "#b3cde3",
        3: "#ccebc5",
        4: "#decbe4",
        5: "#fed9a6",
        6: "#ffffcc",
        7: "#e5d8bd"
    }
    regional_id = feature["properties"].get("id", None)
    cor = cores.get(regional_id, "#fddaec")
    return {
        "fillOpacity": 0.4,
        "fillColor": cor,
        "color": "black",
        "weight": 2,
        "dashArray": "5,5"
    }

## Criar Mapa e separar as UPs como FeatureGroups ##
contagem_base = fol.Map(location=[-19.88589, -44.07113], zoom_start=12.18, tiles="OpenStreetMap",
                         max_zoom=20, crs='EPSG4326')
up_comu = fol.FeatureGroup(name="Unidade Produtiva Comunitária")
up_inst = fol.FeatureGroup(name="Unidade Produtiva Institucional")
up_hibrida = fol.FeatureGroup(name="Unidade Produtiva Institucional/Comunitária")
feira_comu = fol.FeatureGroup(name="Feira Comunitária")

# Adicionar os pontos (Marcadores) com base no GeoDataFrame
for _, row in gdf_ups.iterrows():
    coord = (row["lat"], row["lon"])
    numeral = row["Numeral"]
    type_color = {
        1: "green",
        2: "blue",
        3: "orange"
    }.get(numeral, "purple")
    
    # Determinar o conteúdo do popup #
    popup_html = f"""<h6><b>{row['Nome']}</b></h6><br>
                     <h7><b>Tipo:</b></h7> {row['Tipo']}<br>
                     <h7><b>Regional:</b></h7> {row['Regional']}"""
    
    # Criar o marcador #
    marker = fol.Marker(
        location=coord,
        popup=fol.Popup(
            html=popup_html,
            parse_html=False,
            lazy=True
        ),
        icon=fol.Icon(color=type_color),
        tooltip=f"Conheça a Unidade Produtiva: {row['Nome']}"
    )
    
    # Adicionar o marcador ao grupo correto dependendo do 'Numeral' #
    if numeral == 1:
        marker.add_to(up_comu)
    elif numeral == 2:
        marker.add_to(up_inst)
    elif numeral == 3:
        marker.add_to(up_hibrida)
    elif numeral == 4:
        marker.add_to(feira_comu)
    else: None

## Adicionar os grupos ao mapa, LayerControl para controle das camadas, LocateControl para centralizar usuário no mapa, e SearchBox para buscar por UPs dentro do mapa ##
fol.GeoJson(
    regionais_json,
    style_function=colorir_regional,
    tooltip=fol.GeoJsonTooltip(fields=["Name"], aliases=["Regional:"]),
    name="Regionais"
).add_to(contagem_base)
up_comu.add_to(contagem_base)
up_inst.add_to(contagem_base)
up_hibrida.add_to(contagem_base)
feira_comu.add_to(contagem_base)
fol.LayerControl().add_to(contagem_base)
LocateControl().add_to(contagem_base)


fol.plugins.Search(
    layer=[up_comu, up_inst, up_hibrida, feira_comu],
    search_label='Nome',
    position='topleft',
    placeholder='Pesquise uma Unidade Produtiva no Município de Contagem'
).add_to(contagem_base)

## Exibir no Streamlit ##
st.title(APP_TITLE)
st.header(APP_SUB_TITLE)
st_map = st_folium(contagem_base, width=750, height=750)
