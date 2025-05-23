# -*- coding: utf-8 -*-
import streamlit as st
import requests
import base64

# --- Constantes (algumas vêm do streamlit_app.py, mas são definidas aqui para auto-suficiência) ---
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem"
PMC_PORTAL_URL = "https://portal.contagem.mg.gov.br"
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
LOGO_PMC_FILENAME = "banner_pmc.png"

# Textos específicos da página "Saiba Mais"
SAIBA_TITULO = "Conheça o CMAUF"
SAIBA_SUBTITULO = "Centro Municipal de Agricultura Urbana e Familiar"
SAIBA_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF)"

# Links para os programas
LINK_CONTAGEM_SEM_FOME = "https://portal.contagem.mg.gov.br/portal/noticias/0/3/67444/prefeitura-lanca-campanha-de-seguranca-alimentar-contagem-sem-fome"
LINK_ALIMENTA_CIDADES = "https://www.gov.br/mds/pt-br/acoes-e-programas/promocao-da-alimentacao-adequada-e-saudavel/alimenta-cidades"


# *** CORREÇÃO AQUI: TEXTAO_CMAUF com HTML limpo de espaços iniciais e formatação aprimorada ***
TEXTAO_CMAUF = f"""
<div style="font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.7; color: #333; padding: 15px; background-color: #fcfcfc; border-radius: 8px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
    <p style="margin-bottom: 1.5em; text-align: justify;">
        Criado pela Prefeitura Municipal de Contagem - MG, o CMAUF combate a insegurança alimentar e fortalece a agricultura sustentável,
        alinhado ao programa municipal <a href="{LINK_CONTAGEM_SEM_FOME}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Contagem Sem Fome</a> e a políticas nacionais como o <a href="{LINK_ALIMENTA_CIDADES}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Alimenta Cidades</a>.
        Sua atuação abrange diversas frentes estratégicas:
    </p>

    <h4 style="color: #0066cc; margin-top: 2em; margin-bottom: 0.8em; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;">Pilares de Atuação:</h4>
    <ul style="list-style-type: none; padding-left: 0;">
        <li style="margin-bottom: 1em; padding-left: 25px; position: relative;">
            <span style="position: absolute; left: 0; top: 0; color: #0066cc; font-size: 1.2em;">&#10003;</span>
            <b style="color: #555;">Capacitação e Apoio Técnico:</b>
            Implanta e acompanha Unidades Produtivas (UPs) em todo o município, oferecendo formação,
            troca de mudas e compostos para subsidiar e qualificar a produção local.
        </li>
        <li style="margin-bottom: 1em; padding-left: 25px; position: relative;">
            <span style="position: absolute; left: 0; top: 0; color: #0066cc; font-size: 1.2em;">&#10003;</span>
            <b style="color: #555;">Sistemas Agroecológicos:</b>
            Promove ativamente a comercialização direta de alimentos e a implementação de tecnologias sociais,
            em sintonia com as Políticas Nacional e Estadual de Agricultura Urbana, visando sustentabilidade e equidade.
        </li>
        <li style="margin-bottom: 1em; padding-left: 25px; position: relative;">
            <span style="position: absolute; left: 0; top: 0; color: #0066cc; font-size: 1.2em;">&#10003;</span>
            <b style="color: #555;">Mapeamento Estratégico:</b>
            Realiza a identificação contínua de demandas e oportunidades para o desenvolvimento de ações concretas,
            desde a otimização da produção de alimentos até o incentivo à criação de pequenos animais.
        </li>
    </ul>

    <h4 style="color: #0066cc; margin-top: 2em; margin-bottom: 0.8em; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;">Tipos de Unidades Produtivas (UPs):</h4>
    <ul style="list-style-type: disc; margin-left: 25px; color: #444;">
        <li style="margin-bottom: 0.7em; text-align: justify;"><b>Comunitárias:</b> Projetos de gestão compartilhada desenvolvidos em áreas públicas ou privadas.</li>
        <li style="margin-bottom: 0.7em; text-align: justify;"><b>Institucionais Públicas:</b> Vinculadas e integradas a equipamentos públicos, como Centros de Referência de Assistência Social (CRAS) e centros de saúde.</li>
        <li style="margin-bottom: 0.7em; text-align: justify;"><b>Pedagógicas Escolares:</b> Iniciativas focadas na educação ambiental e na promoção de hábitos alimentares saudáveis no ambiente escolar.</li>
        <li style="margin-bottom: 0.7em; text-align: justify;"><b>Territórios de Tradição:</b> Englobam comunidades quilombolas, terreiros e outras comunidades tradicionais, valorizando seus saberes e práticas.</li>
    </ul>

    <p style="margin-top: 2em; text-align: justify;">
        Adicionalmente, o CMAUF mantém uma parceria estratégica com a EMATER-MG, garantindo assistência técnica especializada
        e extensão rural a agricultores familiares do município. Essa colaboração reforça o compromisso do Centro com o
        desenvolvimento sustentável local e a melhoria contínua da qualidade de vida dos cidadãos de Contagem.
    </p>

    <p style="margin-top: 1.5em; font-style: italic; color: #666; text-align: justify;">
        Vinculado à Diretoria de Agricultura Urbana e Familiar (Subsecretaria de Segurança Alimentar e Nutricional - SUSANA),
        o CMAUF se posiciona como um agente transformador das realidades locais, conectando o campo e a cidade
        por meio de práticas inovadoras e inclusivas.
    </p>
</div>
"""


# Nomes base dos arquivos para os banners do rodapé
BANNER_PMC_BASE_FILENAMES_RODAPE = ["governo_federal.png", "alimenta_cidades.png", "contagem_sem_fome.png"]
FOOTER_BANNER_FILENAMES = BANNER_PMC_BASE_FILENAMES_RODAPE + [LOGO_PMC_FILENAME]

# URLs para os banners do rodapé
BANNER_PMC_URLS_RODAPE = [ICONES_URL_BASE + fname for fname in FOOTER_BANNER_FILENAMES]
LOGO_PMC_URL_CABEÇALHO = ICONES_URL_BASE + LOGO_PMC_FILENAME


# --- Funções de Cache de Imagem ---
@st.cache_data(show_spinner=False)
def get_image_as_base64(image_url: str) -> str | None:
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        img_bytes = response.content
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

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=SAIBA_TITULO, layout="wide", initial_sidebar_state="expanded")

    # Injeção de CSS para ocultar APENAS a lista de navegação de páginas na sidebar
    # E para o alinhamento de colunas
    st.markdown(
        """
        <style>
        .stApp > header {
            position: relative;
            z-index: 1000;
        }

        /* Esconde APENAS a lista de navegação de páginas na sidebar */
        /* Usando uma especificidade maior e !important para garantir */
        nav[data-testid="stSidebarNav"] ul {
            display: none !important;
        }

        /* Os contêineres das colunas do Streamlit são div com data-testid="stVerticalBlock" dentro de div com data-testid="stColumns" */
        /* Para alinhar o conteúdo interno das colunas ao topo */
        div[data-testid="stColumns"] > div > div {
            display: flex;
            flex-direction: column;
            justify-content: flex-start; /* Alinha os itens à parte de cima */
            height: 100%; /* Garante que a coluna ocupa a altura total */
        }

        /* Ajuste específico para o subtítulo para remover margens padrão indesejadas */
        div[data-testid="stVerticalBlock"] h3 {
            margin-top: 0px;
            margin-bottom: 0px;
            padding-top: 0px;
            padding-bottom: 0px;
        }

        /* Ajuste para o logo da PMC na col2 */
        div[data-testid="column-PMC-logo"] {
            display: flex;
            align-items: flex-start; /* Alinha o item ao topo */
            justify-content: center; /* Centraliza horizontalmente */
            height: 100%; /* Ocupa a altura total do flex container */
            margin-top: 44px; /* Desce o contêiner do logo para alinhar com o título */
        }

        /* Regra para a imagem do logo dentro do seu contêiner */
        div[data-testid="column-PMC-logo"] img {
            max-width: 100%; /* Garante que a imagem não exceda a largura da coluna */
            height: auto;    /* Mantém a proporção */
            object-fit: contain; /* Garante que a imagem se ajuste sem cortar */
        }
        </style>
        """, unsafe_allow_html=True
    )

    with st.container():
        col1, col2 = st.columns([3, 0.5])
        
        with col1:
            st.title(SAIBA_TITULO)
            st.header(SAIBA_SUBTITULO)
            if st.button("Voltar ao Mapa"):
                st.switch_page("streamlit_app.py")
            
        with col2:
            st.markdown('<div data-testid="column-PMC-logo">', unsafe_allow_html=True)
            logo_bytes = get_image_bytes(LOGO_PMC_URL_CABEÇALHO)
            if logo_bytes:
                st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="data:image/png;base64,{base64.b64encode(logo_bytes).decode()}"></a>', unsafe_allow_html=True)
            else:
                st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="{LOGO_PMC_URL_CABEÇALHO}"></a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption(SAIBA_DESC)

    # Conteúdo principal da página "Saiba Mais"
    st.markdown(TEXTAO_CMAUF, unsafe_allow_html=True)

    st.markdown("---")

    BANNER_RODAPE_HEIGHT_PX = 80

    def display_banner_html(url: str, height_px: int) -> str:
        base64_image_data = get_image_as_base64(url)
        image_source = base64_image_data if base64_image_data else url

        return f"""
        <div style="
            display: flex;
            justify-content: center;
            align-items: center;
            height: {height_px}px;
            overflow: hidden;
            width: 100%;
        ">
            <img src="{image_source}" alt="Banner" style="
                height: 100%;
                width: auto;
                max-width: 100%;
                object-fit: contain;
                display: block;
            ">
        </div>
        """

    if BANNER_PMC_URLS_RODAPE:
        num_banners = len(BANNER_PMC_URLS_RODAPE)
        num_cols = min(num_banners, 4)

        cols_banner = st.columns(num_cols)

        for i, url in enumerate(BANNER_PMC_URLS_RODAPE):
            with cols_banner[i % num_cols]:
                banner_html = display_banner_html(url, BANNER_RODAPE_HEIGHT_PX)
                st.markdown(banner_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
