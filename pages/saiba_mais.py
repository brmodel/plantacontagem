# -*- coding: utf-8 -*-
import streamlit as st
import requests
import base64
import html # Importar o módulo html para escape
import os # Para manipular extensões de arquivo

# --- Constantes ---
# URL base para as fotos no GitHub (para acesso direto às imagens)
PHOTOS_URL_BASE = "https://raw.githubusercontent.com/brmodel/plantacontagem/main/images/fotos/"
# URL da API do GitHub para listar o conteúdo da pasta (para buscar nomes de arquivos)
GITHUB_API_FOLDER_URL = "https://api.github.com/repos/brmodel/plantacontagem/contents/images/fotos"

# Extensões de arquivo de imagem comuns que serão consideradas
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.ico')

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
    st.set_page_config(page_title="Carrossel de Imagens", layout="wide", initial_sidebar_state="collapsed")

    # Injeção de CSS customizado para o carrossel e estilo geral
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
            max-width: 800px; /* Largura máxima do carrossel */
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

    st.title("Carrossel de Imagens do CMAUF")
    st.write("Confira algumas fotos das atividades e locais do Centro Municipal de Agricultura Urbana e Familiar.")

    # Busca os nomes dos arquivos de imagem dinamicamente do GitHub
    photo_filenames = get_github_image_filenames(GITHUB_API_FOLDER_URL)

    if not photo_filenames:
        st.warning("Não foi possível carregar as imagens do GitHub ou a pasta está vazia.")
        return # Sai da função main se não houver imagens

    # Carregar todas as imagens e convertê-las para base64
    image_data_list = []
    for filename in photo_filenames:
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
        return

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
    st.write("Este carrossel demonstra a integração de recursos web personalizados no Streamlit.")

if __name__ == "__main__":
    main()
