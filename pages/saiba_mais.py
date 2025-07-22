# -*- coding: utf-8 -*-
import streamlit as st
import requests
import base64
import html # Importar o módulo html para escape
import os # Para manipular extensões de arquivo

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
LINK_PAA = "https://www.gov.br/secom/pt-br/acesso-a-informacao/comunicabr/lista-de-acoes-e-programas/programa-de-aquisicao-de-alimentos-paa"

# --- Constantes para o rodapé ---
# Estrutura de dados para gerenciar os banners, com escala e offset vertical.
# Valores de escala e offset ajustados para melhor alinhamento visual.
FOOTER_BANNERS_DATA = [
    {
        "filename": "governo_federal.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/governo_federal.png",
        "link": LINK_GOVERNO_FEDERAL,
        "scale": 2.2,
        "offset_y": -5 # Desloca 10px para cima para alinhar com a imagem ao lado
    },
    {
        "filename": "alimenta_cidades.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/alimenta_cidades.png",
        "link": LINK_ALIMENTA_CIDADES,
        "scale": 2.5,
        "offset_y": -25
    },
    {
        "filename": "contagem_sem_fome.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/contagem_sem_fome.png",
        "link": LINK_CONTAGEM_SEM_FOME,
        "scale": 1.0,
        "offset_y": 25
    },
    {
        "filename": "banner_pmc.png",
        "url": "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/logos/banner_pmc.png",
        "link": PMC_PORTAL_URL,
        "scale": 1.0,
        "offset_y": 25
    }
]

# --- Conteúdo HTML ---
html_content = f"""
<div style="font-family: 'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.7; color: #333; padding: 15px; background-color: #fcfcfc; border-radius: 8px; border: 1px solid #eee; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
<p style="margin-bottom: 1.5em; text-align: justify;">
Centro Municipal de Agricultura Urbana e Familiar (CMAUF) foi criado pela Prefeitura de Contagem para combater a insegurança alimentar através do fortalecimento da agricultura sustentável no município, garantindo o direito humano universal à Segurança Alimentar Nutricional Sustentável. Isso é feito ao fomentar ações de incentivo à produção, ao processamento e à comercialização de alimentos, através da implantação de sistemas produtivos agroecológicos e da comercialização direta dos produtos.
</p>
<p style="margin-bottom: 1.5em; text-align: justify;">
O equipamento trabalha em consonância com as Políticas Nacional e Estadual de Agricultura Urbana Periurbana e Familiar, promovendo programas públicos em nível municipal como o <a href="{LINK_CONTAGEM_SEM_FOME}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Contagem Sem Fome</a>, além de conferir capilaridade a políticas nacionais como o <a href="{LINK_ALIMENTA_CIDADES}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Alimenta Cidades</a>, sendo Contagem um dos municípios exemplares contemplados por esse programa do Governo Federal. Além desses dois, o CMAUF e a Prefeitura de Contagem participam ativamente do <a href="{LINK_PAA}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">Programa de Aquisição de Alimentos (PAA)</a>
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

# --- Constantes para Imagens Estáticas (Galeria) ---
PHOTOS_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/fotos/"
# Extensões de arquivo de imagem comuns que serão consideradas (mantidas para referência, mas não usadas para busca dinâmica)
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.ico')

# --- Funções de Cache ---

@st.cache_data(show_spinner=False)
def get_image_bytes(image_url: str) -> bytes | None:
    """
    Carrega os bytes de uma imagem a partir de uma URL e os armazena em cache.
    Esta função é usada para o logo do cabeçalho.
    """
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
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f0f2f6;
        }}
        .stApp {{
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            background-color: white;
        }}
        /* Estilo para as imagens nas colunas da galeria */
        .stColumn img {{
            width: 100%; /* Ocupa toda a largura da coluna */
            height: auto; /* Mantém a proporção */
            max-height: 200px; /* Altura máxima para as imagens da galeria (aumentada) */
            object-fit: contain; /* Garante que a imagem caiba sem cortar */
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin: 5px auto; /* Centraliza a imagem na coluna */
            display: block; /* Garante que margin: auto funcione */
        }}
        /* Para alinhar o texto da legenda abaixo da imagem */
        .stCaption {{
            text-align: center;
            font-size: 0.85em;
            color: #666;
            margin-top: 5px;
        }}
        /* Estilo para a imagem 1.jpg em destaque */
        .top-image-container {{
            width: 100%;
            display: flex;
            justify-content: center;
            margin-top: 20px; /* Espaço antes da imagem */
            margin-bottom: 20px; /* Espaço depois da imagem */
        }}
        .top-image-container img {{
            max-width: 250px; /* Largura máxima para a imagem principal (reduzida em ~200%) */
            width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
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

    # --- Conteúdo Principal (Texto) ---
    st.markdown(html_content, unsafe_allow_html=True)

    st.markdown("---") # Separador após o conteúdo principal

    # --- Imagem 1.jpg em destaque (agora após o conteúdo principal) ---
    st.markdown('<div class="top-image-container">', unsafe_allow_html=True)
    st.image(PHOTOS_URL_BASE + "1.jpg", caption="Foto de Destaque") # Removido use_column_width
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---") # Separador após a imagem de destaque

    # --- Galeria de Imagens Estáticas (fotos de 2 a 9) ---
    # Removido o título e subtítulo da galeria

    # Lista de URLs das imagens a serem exibidas (fotos de 2 a 9)
    images_to_display = [
        PHOTOS_URL_BASE + "2.jpeg",
        PHOTOS_URL_BASE + "3.png",
        PHOTOS_URL_BASE + "4.jpg",
        PHOTOS_URL_BASE + "5.jpeg",
        PHOTOS_URL_BASE + "6.png",
        PHOTOS_URL_BASE + "7.jpg",
        PHOTOS_URL_BASE + "8.jpeg",
        PHOTOS_URL_BASE + "9.png",
    ]

    if not images_to_display:
        st.warning("Nenhuma imagem para exibir na galeria. Por favor, verifique os nomes dos arquivos.")
    else:
        num_images_per_row = 3 # Retornado para 3 colunas
        
        # Divide as imagens em linhas de 3
        for i in range(0, len(images_to_display), num_images_per_row):
            cols = st.columns(num_images_per_row)
            for j in range(num_images_per_row):
                if i + j < len(images_to_display):
                    with cols[j]:
                        img_url = images_to_display[i + j]
                        # Usar st.image diretamente com a URL, permitindo que o CSS controle o tamanho
                        st.image(img_url)
                        # Adicionar uma legenda base para cada foto
                        st.caption(f"Legenda da Foto {i + j + 2}") # Ajustado o índice para começar de 2
                else:
                    # Preencher colunas vazias se não houver imagens suficientes para a última linha
                    with cols[j]:
                        st.empty() # Garante que as colunas vazias não quebrem o layout

    st.markdown("---")

    # --- Layout do Rodapé ---
    def display_banner_html(url: str, filename: str, link_url: str | None, scale: float = 1.0, offset_y: int = 0) -> str:
        """Gera o HTML para um banner com escala e deslocamento vertical."""
        escaped_url = html.escape(url)
        escaped_filename = html.escape(filename)

        base_max_height_px = 50
        scaled_max_height = int(base_max_height_px * scale)

        offset_style = f"margin-top: {offset_y}px;" if offset_y != 0 else ""

        # CORREÇÃO: Os estilos CSS são juntados em uma única string sem quebras de linha.
        img_style_parts = [
            "height: auto",
            "width: auto",
            "max-width: 100%",
            f"max-height: {scaled_max_height}px",
            "object-fit: contain",
            "display: block",
            "margin-left: auto",
            "margin-right: auto",
            offset_style
        ]
        img_style = "; ".join(filter(None, [s.strip() for s in img_style_parts]))

        image_tag = f'<img src="{escaped_url}" alt="Banner {escaped_filename}" style="{img_style}">'

        # CORREÇÃO: Estilos do container também em uma única linha.
        container_style_parts = [
            "display: flex",
            "justify-content: center",
            "align-items: center",
            f"min-height: {scaled_max_height}px",
            "overflow: hidden",
            "width: 100%",
            "padding: 5px",
        ]
        container_style = "; ".join(filter(None, [s.strip() for s in container_style_parts]))

        if link_url:
            return f'<div style="{container_style}"><a href="{link_url}" target="_blank" rel="noopener noreferrer">{image_tag}</a></div>'
        else:
            return f'<div style="{container_style}">{image_tag}</div>'

    # Cria colunas para cada banner no rodapé
    cols_banner = st.columns(len(FOOTER_BANNERS_DATA))

    # Itera sobre os dados dos banners e exibe cada um em sua coluna com a escala e offset corretos
    for i, banner_data in enumerate(FOOTER_BANNERS_DATA):
        with cols_banner[i]:
            banner_html = display_banner_html(
                url=banner_data["url"],
                filename=banner_data["filename"],
                link_url=banner_data["link"],
                scale=banner_data.get("scale", 1.0),
                offset_y=banner_data.get("offset_y", 0)
            )
            st.markdown(banner_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
