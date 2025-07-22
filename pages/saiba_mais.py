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

# --- Constantes para o Carrossel de Imagens ---
# URL base para as fotos no GitHub (para acesso direto às imagens)
PHOTOS_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/fotos/"
# URL da API do GitHub para listar o conteúdo da pasta (para buscar nomes de arquivos)
GITHUB_API_FOLDER_URL = "https://api.github.com/repos/brmodel/plantacontagem/contents/images/fotos"

# Extensões de arquivo de imagem comuns que serão consideradas
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.ico')

# Limite de imagens a serem carregadas no carrossel para otimização
MAX_CAROUSEL_IMAGES = 20 # Limita a 20 imagens para evitar sobrecarga

# --- Funções de Cache ---

@st.cache_data(show_spinner="Buscando nomes de arquivos de imagem no GitHub...")
def get_github_image_filenames(api_url: str) -> list[str]:
    """
    Busca os nomes dos arquivos de imagem em uma pasta do GitHub usando a API.
    Retorna uma lista de nomes de arquivos.
    """
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status() # Levanta um erro para códigos de status HTTP ruins
        contents = response.json()

        filenames = []
        for item in contents:
            if item['type'] == 'file':
                # Verifica se a extensão do arquivo está na lista de extensões de imagem
                _, ext = os.path.splitext(item['name'])
                if ext.lower() in IMAGE_EXTENSIONS:
                    filenames.append(item['name'])
        return filenames
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar nomes de arquivos do GitHub: {e}")
        return []
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao processar a resposta do GitHub: {e}")
        return []

@st.cache_data(show_spinner=False)
def get_image_bytes(image_url: str) -> bytes | None:
    """
    Carrega os bytes de uma imagem a partir de uma URL e os armazena em cache.
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao carregar a imagem de {image_url}: {e}")
        return None

# --- App Principal Streamlit ---
def main():
    st.set_page_config(page_title=SAIBA_TITULO, layout="wide", initial_sidebar_state="collapsed")

    # Injeção de CSS customizado
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

        body {
            font-family: 'Inter', sans-serif;
            background-color: #f0f2f6;
        }
        .stApp {
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            background-color: white;
        }

        .carousel-container {
            position: relative;
            width: 100%;
            max-width: 600px; /* Largura média do carrossel */
            margin: 20px auto;
            overflow: hidden;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            background-color: #f8f8f8;
            aspect-ratio: 16 / 9; /* Mantém a proporção 16:9 */
        }

        .carousel-slide {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            transition: opacity 1s ease-in-out; /* Efeito crossfade */
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #eee; /* Cor de fundo enquanto a imagem carrega */
        }

        .carousel-slide.active {
            opacity: 1;
        }

        .carousel-slide img {
            width: 100%;
            height: 100%;
            object-fit: contain; /* Ajusta a imagem para caber sem cortar */
            border-radius: 10px;
        }

        .carousel-button {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background-color: rgba(0, 0, 0, 0.6);
            color: white;
            border: none;
            padding: 12px 18px;
            cursor: pointer;
            font-size: 24px;
            border-radius: 50%;
            z-index: 10;
            transition: background-color 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .carousel-button:hover {
            background-color: rgba(0, 0, 0, 0.8);
        }

        .prev {
            left: 10px;
        }

        .next {
            right: 10px;
        }

        /* Indicadores de slide */
        .carousel-indicators {
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 8px;
            z-index: 10;
        }

        .indicator-dot {
            width: 12px;
            height: 12px;
            background-color: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .indicator-dot.active {
            background-color: rgba(255, 255, 255, 1);
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

    # --- Carrossel de Imagens (Adicionado aqui) ---
    st.subheader("Galeria de Fotos do CMAUF")
    st.write("Confira algumas fotos das atividades e locais do Centro Municipal de Agricultura Urbana e Familiar.")

    # Busca os nomes dos arquivos de imagem dinamicamente do GitHub
    photo_filenames = get_github_image_filenames(GITHUB_API_FOLDER_URL)

    if not photo_filenames:
        st.warning("Não foi possível carregar as imagens do GitHub ou a pasta está vazia.")
    else:
        # Limita o número de imagens a serem carregadas
        photo_filenames_limited = photo_filenames[:MAX_CAROUSEL_IMAGES]

        # Carregar todas as imagens e convertê-las para base64
        image_data_list = []
        for filename in photo_filenames_limited:
            image_url = PHOTOS_URL_BASE + filename
            img_bytes = get_image_bytes(image_url)
            if img_bytes:
                # Usar html.escape para garantir que a string base64 seja segura para HTML
                # Determinar o tipo MIME da imagem com base na extensão
                _, ext = os.path.splitext(filename)
                mime_type = f"image/{ext[1:]}" if ext else "image/jpeg" # Default para jpeg se não houver extensão
                if ext.lower() == '.jpg': # Ajuste específico para .jpg que é frequentemente image/jpeg
                    mime_type = "image/jpeg"
                elif ext.lower() == '.gif':
                    mime_type = "image/gif"
                elif ext.lower() == '.webp':
                    mime_type = "image/webp"

                encoded_image = html.escape(base64.b64encode(img_bytes).decode())
                image_data_list.append((encoded_image, mime_type))
            else:
                st.warning(f"Não foi possível carregar a imagem: {filename}. Será ignorada no carrossel.")
                # Não adicionamos None para evitar slides vazios, apenas ignoramos a imagem com erro

        if not image_data_list:
            st.warning("Nenhuma imagem válida foi carregada para o carrossel.")
        else:
            # Construir o HTML do carrossel
            carousel_slides_html = ""
            carousel_indicators_html = ""
            for i, (encoded_img, mime_type) in enumerate(image_data_list):
                # O primeiro slide é ativo por padrão
                active_class = "active" if i == 0 else ""
                carousel_slides_html += f"""
                <div class="carousel-slide {active_class}">
                    <img src="data:{mime_type};base64,{encoded_img}" alt="Foto {i+1}">
                </div>
                """
                
                # Indicadores de slide
                active_dot_class = "active" if i == 0 else ""
                carousel_indicators_html += f"""
                <div class="indicator-dot {active_dot_class}" onclick="currentSlide({i})"></div>
                """

            carousel_html = f"""
            <div class="carousel-container">
                {carousel_slides_html}
                <button class="carousel-button prev" onclick="moveSlide(-1)">&#10094;</button>
                <button class="carousel-button next" onclick="moveSlide(1)">&#10095;</button>
                <div class="carousel-indicators">
                    {carousel_indicators_html}
                </div>
            </div>

            <script>
                let slideIndex = 0;
                const slides = document.querySelectorAll('.carousel-slide');
                const dots = document.querySelectorAll('.indicator-dot');
                const totalSlides = slides.length;

                function showSlides() {{
                    for (let i = 0; i < totalSlides; i++) {{
                        slides[i].classList.remove('active');
                        dots[i].classList.remove('active');
                    }}
                    slides[slideIndex].classList.add('active');
                    dots[slideIndex].classList.add('active');
                }}

                function moveSlide(n) {{
                    slideIndex += n;
                    if (slideIndex >= totalSlides) {{ slideIndex = 0; }}
                    if (slideIndex < 0) {{ slideIndex = totalSlides - 1; }}
                    showSlides();
                }}

                function currentSlide(n) {{
                    slideIndex = n;
                    showSlides();
                }}

                // Auto-play
                setInterval(() => moveSlide(1), 5000); // Muda de slide a cada 5 segundos

                // Exibe o primeiro slide ao carregar
                showSlides();
            </script>
            """

            # Exibir o carrossel no Streamlit
            st.markdown(carousel_html, unsafe_allow_html=True)

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
