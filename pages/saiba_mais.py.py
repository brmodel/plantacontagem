# -*- coding: utf-8 -*-
import streamlit as st
import requests
import base64

# --- Constantes (algumas vêm do streamlit_app.py, mas são definidas aqui para auto-suficiência) ---
# Se estas constantes mudarem no streamlit_app.py, você precisará atualizá-las aqui também.
# Uma alternativa mais avançada seria importar de um arquivo de configuração comum,
# mas para simplicidade, vamos duplicá-las aqui.
APP_TITULO = "Planta Contagem"
APP_SUBTITULO = "Mapa das Unidades Produtivas de Contagem" # Mantido para consistência de estilo de cabeçalho
PMC_PORTAL_URL = "https://portal.contagem.mg.gov.br" # URL do portal da PMC
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/"
LOGO_PMC_FILENAME = "banner_pmc.png" # Arquivo do logo da PMC, também usado como banner no rodapé

# Textos específicos da página "Saiba Mais"
SAIBA_TITULO = "Conheça o CMAUF"
SAIBA_SUBTITULO = "Centro Municipal de Agricultura Urbana e Familiar"
SAIBA_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF)"

TEXTAO_CMAUF = """
<div style="font-family: Arial, sans-serif; font-size: 16px; line-height: 1.6; padding: 15px; background-color: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
    <p style="margin-bottom: 1em;">Criado pela Prefeitura Municipal de Contagem - MG, o CMAUF combate a insegurança alimentar e fortalece a agricultura sustentável, alinhado ao programa municipal <b>Contagem Sem Fome</b> e a políticas nacionais como o <b>Alimenta Cidades</b>. Sua atuação inclui:</p>

    <ul style="list-style-type: disc; margin-left: 20px; padding-left: 0;">
        <li style="margin-bottom: 0.5em;"><b>Capacitação e apoio técnico:</b> implanta e acompanha Unidades Produtivas (UPs) em todo o município, oferecendo formação, troca de mudas e compostos para subsidiar a produção.</li>
        <li style="margin-bottom: 0.5em;"><b>Sistemas agroecológicos:</b> promove a comercialização direta de alimentos e tecnologias sociais, em sintonia com as Políticas Nacional e Estadual de Agricultura Urbana.</li>
        <li style="margin-bottom: 0.5em;"><b>Mapeamento estratégico:</b> identifica demandas e oportunidades para ações concretas, desde produção de alimentos até criação de pequenos animais.</li>
    </ul>

    <p style="margin-top: 1em; margin-bottom: 0.5em;">O equipamento trabalha com quatro tipos de UPs:</p>
    <ul style="list-style-type: circle; margin-left: 30px; padding-left: 0;">
        <li style="margin-bottom: 0.3em;"><b>Comunitárias</b>: gestão compartilhada em áreas públicas ou privadas;</li>
        <li style="margin-bottom: 0.3em;"><b>Institucionais Públicas</b>: vinculadas a equipamentos como CRAS e centros de saúde;</li>
        <li style="margin-bottom: 0.3em;"><b>Pedagógicas Escolares</b>: foco em educação ambiental e consumo saudável;</li>
        <li style="margin-bottom: 0.3em;"><b>Territórios de Tradição</b>: quilombos, terreiros e comunidades tradicionais.</li>
    </ul>

    <p style="margin-top: 1em;">Além disso, o CMAUF conta com uma parceria estratégica com a EMATER-MG, garantindo assistência a agricultores familiares do município, reforçando o compromisso com desenvolvimento sustentável e qualidade de vida.</p>

    <p style="margin-top: 1em;">Vinculado à Diretoria de Agricultura Urbana e Familiar (Subsecretaria SUSANA), o CMAUF transforma realidades locais, conectando campo e cidade através de práticas inovadoras.</p>
</div>
"""


# Nomes base dos arquivos para os banners do rodapé
BANNER_PMC_BASE_FILENAMES_RODAPE = ["governo_federal.png", "alimenta_cidades.png", "contagem_sem_fome.png"]
# LOGO_PMC_FILENAME já definido acima.
FOOTER_BANNER_FILENAMES = BANNER_PMC_BASE_FILENAMES_RODAPE + [LOGO_PMC_FILENAME]

# URLs para os banners do rodapé (agora incluindo o banner_pmc.png)
BANNER_PMC_URLS_RODAPE = [ICONES_URL_BASE + fname for fname in FOOTER_BANNER_FILENAMES]
LOGO_PMC_URL_CABEÇALHO = ICONES_URL_BASE + LOGO_PMC_FILENAME


# --- Funções de Cache de Imagem (replicadas para auto-suficiência da página) ---
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
    st.set_page_config(page_title=SAIBA_TITULO, layout="wide", initial_sidebar_state="collapsed")

    # Injeção de CSS para alinhar verticalmente e outros estilos
    st.markdown(
        """
        <style>
        .stApp > header {
            position: relative;
            z-index: 1000;
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

    # st.navigation para navegar entre as páginas com hidden=True
    st.navigation([
        st.Page("streamlit_app.py", title="Mapa", url_path="/mapa", hidden=True),
        st.Page("pages/saiba_mais.py", title="Saiba Mais", url_path="/saiba_mais", hidden=True)
    ])

    with st.container():
        col1, col2 = st.columns([3, 0.5]) # Ajustado o peso da col2 para o logo
        
        with col1:
            st.title(SAIBA_TITULO)
            st.header(SAIBA_SUBTITULO)
            # Botão para voltar ao mapa
            if st.button("Voltar ao Mapa"):
                st.switch_page("streamlit_app.py")

        with col2:
            # Adiciona um data-testid para o CSS customizado e aplica o margin-top
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
    st.markdown(TEXTAO_CMAUF, unsafe_allow_html=True) # Usamos TEXTAO_CMAUF agora.

    st.markdown("---") # Separador antes dos banners do rodapé

    # Defina a altura desejada para os banners do rodapé (em pixels)
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
                height: 100%; /* Prioriza a altura total do contêiner */
                width: auto;  /* Permite que a largura se ajuste automaticamente */
                max-width: 100%; /* Garante que a imagem não ultrapasse a largura da coluna */
                object-fit: contain; /* Mantém a proporção e se ajusta ao contêiner */
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
