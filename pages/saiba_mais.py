# -*- coding: utf-8 -*-
import streamlit as st
import requests
import base64

# --- Constantes ---
PMC_PORTAL_URL = "https://portal.contagem.mg.gov.br"
# URLs base para as imagens no GitHub
ICONES_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/icones/"
BANNER_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/"
LOGO_PMC_FILENAME = "banner_pmc.png"

# --- Textos da Página ---
SAIBA_TITULO = "Conheça o CMAUF"
SAIBA_SUBTITULO = "Centro Municipal de Agricultura Urbana e Familiar"
SAIBA_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF)"

# --- Links ---
LINK_CONTAGEM_SEM_FOME = "https://portal.contagem.mg.gov.br/portal/noticias/0/3/67444/prefeitura-lanca-campanha-de-seguranca-alimentar-contagem-sem-fome"
LINK_ALIMENTA_CIDADES = "https://www.gov.br/mds/pt-br/acoes-e-programas/promocao-da-alimentacao-adequada-e-saudavel/alimenta-cidades"

# --- Constantes para o rodapé ---
BANNER_PMC_BASE_FILENAMES_RODAPE = ["governo_federal.png", "alimenta_cidades.png", "contagem_sem_fome.png"]
FOOTER_BANNER_FILENAMES = BANNER_PMC_BASE_FILENAMES_RODAPE + [LOGO_PMC_FILENAME]
BANNER_PMC_URLS_RODAPE = [BANNER_URL_BASE + fname for fname in FOOTER_BANNER_FILENAMES]

NORMAL_BANNER_SCALE = 1.0
LARGE_BANNER_SCALE_RODAPE = 1.25 # Nova escala para as duas primeiras logos do rodapé
FIRST_TWO_FOOTER_BANNERS = ["governo_federal.png", "alimenta_cidades.png"] # Nomes das duas primeiras logos
LAST_TWO_FOOTER_BANNERS = ["contagem_sem_fome.png", "banner_pmc.png"]
OFFSET_LOGO_PX = 40 # Valor para o deslocamento vertical negativo


# --- Conteúdo HTML ---
html_content = f"""
<div style="font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.7; color: #333; padding: 15px; background-color: #fcfcfc; border-radius: 8px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
<p style="margin-bottom: 1.5em; text-align: justify;">
Centro Municipal de Agricultura Urbana e Familiar (CMAUF) foi criado pela Prefeitura de Contagem para combater a insegurança alimentar através do fortalecimento da agricultura sustentável no município, garantindo o direito humano universal à Segurança Alimentar Nutricional Sustentável. Isso é feito ao fomentar ações de incentivo à produção, ao processamento e à comercialização de alimentos, através da implantação de sistemas produtivos agroecológicos e da comercialização direta dos produtos.
</p>
<p style="margin-bottom: 1.5em; text-align: justify;">
O equipamento trabalha em consonância com as Políticas Nacional e Estadual de Agricultura Urbana Periurbana e Familiar, promovendo programas públicos em nível municipal como o <a href="{LINK_CONTAGEM_SEM_FOME}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Contagem Sem Fome</a>, além de conferir capilaridade a políticas nacionais como o <a href="{LINK_ALIMENTA_CIDADES}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Alimenta Cidades</a>, sendo Contagem um dos municípios exemplares contemplados por esse programa do Governo Federal.
</p>
<h4 style="color: #0066cc; margin-top: 2em; margin-bottom: 0.8em; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;">Pilares de Atuação:</h4>
<ul style="list-style-type: none; padding-left: 0;">
<li style="margin-bottom: 1em; padding-left: 25px; position: relative;">
<span style="position: absolute; left: 0; top: 0; color: #0066cc; font-size: 1.2em;">&#10003;</span>
<b style="color: #555;">Capacitação e apoio técnico:</b>
Implanta e acompanha Unidades Produtivas (UPs) em todo o município, oferecendo assistência e formação técnica, trocas de mudas, subsidiando e qualificando a produção local.
</li>
<li style="margin-bottom: 1em; padding-left: 25px; position: relative;">
<span style="position: absolute; left: 0; top: 0; color: #0066cc; font-size: 1.2em;">&#10003;</span>
<b style="color: #555;">Sistemas agroecológicos:</b>
Promove ativamente a comercialização direta de alimentos e a implementação de tecnologias sociais,
em sintonia com as Políticas Nacional e Estadual de Agricultura Urbana, visando sustentabilidade e equidade.
</li>
<li style="margin-bottom: 1em; padding-left: 25px; position: relative;">
<span style="position: absolute; left: 0; top: 0; color: #0066cc; font-size: 1.2em;">&#10003;</span>
<b style="color: #555;">Mapeamento estratégico:</b>
Realiza a identificação contínua de demandas e oportunidades para o desenvolvimento de ações concretas,
desde a otimização da produção de alimentos até o incentivo à criação de pequenos animais.
</li>
<p style="margin-top: 2em; text-align: justify;">
Para tanto, o CMAUF é formado por uma dupla parceria entre a Organização da Sociedade Civil da Comunidade Quilombola dos Arturo's, e mantém uma parceria estratégica com a EMATER-MG, garantindo assistência técnica especializada
e extensão rural a agricultores familiares do município e para os vários tipos de Unidades Produtivas. Essa colaboração reforça o compromisso da prefeitura com o
desenvolvimento sustentável local e a melhoria contínua da qualidade de vida dos cidadãos de Contagem.
</p>
</ul>
<h4 style="color: #0066cc; margin-top: 2em; margin-bottom: 0.8em; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;">Tipos de Unidades Produtivas (UPs):</h4>
<ul style="list-style-type: disc; margin-left: 25px; color: #444;">
<li style="margin-bottom: 0.7em; text-align: justify;"><b>Comunitárias:</b> Projetos de gestão compartilhada desenvolvidos em áreas públicas ou privadas.</li>
<li style="margin-bottom: 0.7em; text-align: justify;"><b>Institucionais:</b> Vinculadas e integradas a equipamentos públicos, como Centros de Referência de Assistência Social (CRAS), Unidades Básicas de Saúde e Escolas Públicas.</li>
<li style="margin-bottom: 0.7em; text-align: justify;"><b>Comunitária/Institucional:</b> Iniciativas focadas na educação ambiental e na promoção de hábitos alimentares saudáveis no ambiente escolar.</li>
<li style="margin-bottom: 0.7em; text-align: justify;"><b>Agricultores Familiares:</b> produtores urbanos e periurbanos do município de Contagem que são atendidos pela parceria com a EMATER.</li>
</ul>
<h4 style="color: #0066cc; margin-top: 2em; margin-bottom: 0.8em; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;">Outras iniciativas em Contagem:</h4>
<ul style="list-style-type: disc; margin-left: 25px; color: #444;">
<li style="margin-bottom: 0.7em; text-align: justify;"><b>Restaurante Popular:</b> Projetos de gestão compartilhada desenvolvidos em áreas públicas ou privadas.</li>
<li style="margin-bottom: 0.7em; text-align: justify;"><b>Banco de Alimentos:</b> Iniciativas focadas na educação ambiental e na promoção de hábitos alimentares saudáveis no ambiente escolar.</li>
<li style="margin-bottom: 0.7em; text-align: justify;"><b>Feiras da Cidade:</b> Vinculadas e integradas a equipamentos públicos, como Centros de Referência de Assistência Social (CRAS) e centros de saúde.</li>
<li style="margin-bottom: 0.7em; text-align: justify;"><b>Viveiros:</b> Iniciativas focadas na educação ambiental e na promoção de hábitos alimentares saudáveis no ambiente escolar.</li>
</ul>
</div>
"""

# --- Funções de Cache de Imagem ---
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

    # Injeção de CSS customizado
    st.markdown(
        """
        <style>
        .stApp > header {
            position: relative;
            z-index: 1000;
        }
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }
        div[data-testid="stColumns"] > div > div {
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            height: 100%;
        }
        div[data-testid="stVerticalBlock"] h3 {
            margin-top: 0px; margin-bottom: 0px;
            padding-top: 0px; padding-bottom: 0px;
        }
        div[data-testid="column-PMC-logo"] {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            padding-top: 5px;
            margin-top: 0px;
        }
        div[data-testid="column-PMC-logo"] img {
            max-width: 100%;
            height: auto;
            max-height: 60px;
            object-fit: contain;
        }
        </style>
        """, unsafe_allow_html=True
    )

    # --- Layout do Cabeçalho ---
    with st.container():
        col1, col2 = st.columns([3, 0.5])
        with col1:
            st.title(SAIBA_TITULO)
            st.header(SAIBA_SUBTITULO)
            if st.button("⬅️ Voltar ao Mapa"):
                st.switch_page("streamlit_app.py")

        with col2:
            st.markdown('<div data-testid="column-PMC-logo">', unsafe_allow_html=True)
            logo_bytes = get_image_bytes(BANNER_URL_BASE + LOGO_PMC_FILENAME)
            if logo_bytes:
                st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="data:image/png;base64,{base64.b64encode(logo_bytes).decode()}"></a>', unsafe_allow_html=True)
            else:
                st.markdown(f'<a href="{PMC_PORTAL_URL}" target="_blank"><img src="{BANNER_URL_BASE + LOGO_PMC_FILENAME}"></a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption(SAIBA_DESC)

    # --- Conteúdo Principal ---
    st.markdown(html_content, unsafe_allow_html=True)

    st.markdown("---")

    # --- Layout do Rodapé ---
    def display_banner_html(url: str, filename: str, scale: float = 1.0, offset_top_px: int = 0) -> str:
        # Usar a URL diretamente, sem tentar base64 para evitar problemas de renderização
        image_source = url
        
        base_max_height_px = 70 
        scaled_max_height = int(base_max_height_px * scale)

        margin_top_style = f"margin-top: {offset_top_px}px;" if offset_top_px else ""

        img_style = f"""
            height: auto; 
            width: auto; /* Alterado para auto */
            max-width: 100%; 
            max-height: {scaled_max_height}px; 
            object-fit: contain; 
            display: block;
            margin-left: auto; 
            margin-right: auto;
            {margin_top_style} 
        """
        
        # Adiciona o link para as imagens do rodapé
        link_url = None
        if filename == "governo_federal.png":
            link_url = "https://www.gov.br/pt-br"
        elif filename == "alimenta_cidades.png":
            link_url = LINK_ALIMENTA_CIDADES
        elif filename == "contagem_sem_fome.png":
            link_url = LINK_CONTAGEM_SEM_FOME
        elif filename == "banner_pmc.png":
            link_url = PMC_PORTAL_URL

        # A tag <img> é construída diretamente com a URL. Removido o onerror redundante.
        image_tag = f'<img src="{image_source}" alt="Banner {filename}" style="{img_style}">'

        if link_url:
            return f"""
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: {scaled_max_height}px;
                overflow: hidden;
                width: 100%;
                padding: 5px;
            ">
                <a href="{link_url}" target="_blank" rel="noopener noreferrer">{image_tag}</a>
            </div>
            """
        else:
            return f"""
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: {scaled_max_height}px;
                overflow: hidden;
                width: 100%;
                padding: 5px;
            ">
                {image_tag}
            </div>
            """

    if BANNER_PMC_URLS_RODAPE:
        num_banners = len(BANNER_PMC_URLS_RODAPE)
        cols_banner = st.columns(num_banners if num_banners <= 4 else 4) 

        for i, url in enumerate(BANNER_PMC_URLS_RODAPE):
            filename = FOOTER_BANNER_FILENAMES[i]
            # Aplica a nova escala apenas para as duas primeiras logos
            if filename in FIRST_TWO_FOOTER_BANNERS:
                current_scale = LARGE_BANNER_SCALE_RODAPE
            else:
                current_scale = NORMAL_BANNER_SCALE 
            
            offset_for_this_logo = OFFSET_LOGO_PX if filename in LAST_TWO_FOOTER_BANNERS else 0
            
            with cols_banner[i % len(cols_banner)]: 
                banner_html = display_banner_html(url, filename, current_scale, offset_for_this_logo)
                st.markdown(banner_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
