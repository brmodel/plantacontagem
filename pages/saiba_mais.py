# -*- coding: utf-8 -*-
import streamlit as st
import requests
import base64
import html # Importar o módulo html para escape

# --- Constantes ---
PMC_PORTAL_URL = "https://portal.contagem.mg.gov.br"
# URLs base para as imagens no GitHub
BANNER_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/"
LOGO_PMC_FILENAME = "banner_pmc.png"

# --- Textos da Página ---
SAIBA_TITULO = "Conheça o CMAUF"
SAIBA_SUBTITULO = "Centro Municipal de Agricultura Urbana e Familiar"
SAIBA_DESC = "Prefeitura Municipal de Contagem - MG, Mapeamento feito pelo Centro Municipal de Agricultura Urbana e Familiar (CMAUF)"

# --- Links ---
LINK_CONTAGEM_SEM_FOME = "https://portal.contagem.mg.gov.br/portal/noticias/0/3/67444/prefeitura-lanca-campanha-de-seguranca-alimentar-contagem-sem-fome"
LINK_ALIMENTA_CIDADES = "https://www.gov.br/mds/pt-br/acoes-e-programas/promocao-da-alimentacao-adequada-e-saudavel/alimenta-cidades"
LINK_GOVERNO_FEDERAL = "https://www.gov.br/pt-br"

# --- Constantes para o rodapé ---
# Estrutura de dados para gerenciar os banners do rodapé de forma mais organizada
FOOTER_BANNERS_DATA = [
    {
        "filename": "governo_federal.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/governo_federal.png",
        "link": LINK_GOVERNO_FEDERAL
    },
    {
        "filename": "alimenta_cidades.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/alimenta_cidades.png",
        "link": LINK_ALIMENTA_CIDADES
    },
    {
        "filename": "contagem_sem_fome.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/contagem_sem_fome.png",
        "link": LINK_CONTAGEM_SEM_FOME
    },
    {
        "filename": "banner_pmc.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/banner_pmc.png",
        "link": PMC_PORTAL_URL
    }
]


# --- Conteúdo HTML ---
html_content = f"""
<div style="font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.7; color: #333; padding: 15px; background-color: #fcfcfc; border-radius: 8px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
<p style="margin-bottom: 1.5em; text-align: justify;">
Centro Municipal de Agricultura Urbana e Familiar (CMAUF) foi criado pela Prefeitura de Contagem para combater a insegurança alimentar através do fortalecimento da agricultura sustentável no município, garantindo o direito humano universal à Segurança Alimentar Nutricional Sustentável. Isso é feito ao fomentar ações de incentivo à produção, ao processamento e à comercialização de alimentos, através da implantação de sistemas produtivos agroecológicos e da comercialização direta dos produtos.
</p>
<p style="margin-bottom: 1.5em; text-align: justify;">
O equipamento trabalha **em** consonância com as Políticas Nacional e Estadual de Agricultura Urbana Periurbana e Familiar, promovendo programas públicos em nível municipal como o <a href="{LINK_CONTAGEM_SEM_FOME}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Contagem Sem Fome</a>, além de conferir capilaridade **a** políticas nacionais como o <a href="{LINK_ALIMENTA_CIDADES}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Alimenta Cidades</a>, sendo Contagem um dos municípios exemplares contemplados por esse programa do Governo Federal.
</p>
<h4 style="color: #0066cc; margin-top: 2em; margin-bottom: 0.8em; font-weight: 600; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px;">Pilares de Atuação:</h4>
<ul style="list-style-type: none; padding-left: 0;">
<li style="margin-bottom: 1em; padding-left: 25px; position: relative;">
<span style="position: absolute; left: 0; top: 0; color: #0066cc; font-size: 1.2em;">&#10003;</span>
<b style="color: #555;">Capacitação e apoio técnico:</b>
Implanta e acompanha Unidades Produtivas (UPs) em todo o município, oferecendo assistência e formação técnica, trocas de mudas, subsidiando e **qualificando** a produção local.
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
Para tanto, o CMAUF é formado **por** uma dupla parceria entre a Organização da Sociedade Civil da Comunidade Quilombola dos Arturo's, e mantém uma parceria estratégica com a EMATER-MG, garantindo assistência técnica especializada
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
    def display_banner_html(url: str, filename: str, link_url: str | None) -> str:
        escaped_url = html.escape(url)
        escaped_filename = html.escape(filename)
        
        # Tamanho base consistente para todas as logos
        base_max_height_px = 70 

        img_style = f"""
            height: auto;
            width: auto;
            max-width: 100%; 
            max-height: {base_max_height_px}px; 
            object-fit: contain; 
            display: block;
            margin-left: auto; 
            margin-right: auto;
        """
        
        image_tag = f'<img src="{escaped_url}" alt="Banner {escaped_filename}" style="{img_style}">'

        # O container div garante alinhamento vertical e centraliza o conteúdo
        container_style = f"""
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: {base_max_height_px}px;
            overflow: hidden;
            width: 100%;
            padding: 5px;
        """

        if link_url:
            return f'<div style="{container_style}"><a href="{link_url}" target="_blank" rel="noopener noreferrer">{image_tag}</a></div>'
        else:
            return f'<div style="{container_style}">{image_tag}</div>'

    # Cria colunas para cada banner no rodapé
    cols_banner = st.columns(len(FOOTER_BANNERS_DATA)) 

    # Itera sobre os dados dos banners e exibe cada um em sua coluna
    for i, banner_data in enumerate(FOOTER_BANNERS_DATA):
        with cols_banner[i]: 
            banner_html = display_banner_html(
                url=banner_data["url"],
                filename=banner_data["filename"],
                link_url=banner_data["link"]
            )
            st.markdown(banner_html, unsafe_allow_html=True)

    # --- Placeholder para o Carrossel de Imagens ---
    st.info("O carrossel de imagens será implementado aqui assim que o link para a pasta de imagens for fornecido.")

if __name__ == "__main__":
    main()
