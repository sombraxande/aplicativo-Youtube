# app.py (Frontend com Streamlit)

import streamlit as st
from datetime import datetime, timedelta, timezone

# Importa as funções do nosso backend (main.py)
from main import buscar_videos_youtube, salvar_no_google_sheets

# --- Configuração da Página ---
st.set_page_config(
    page_title="Youtube Tool",
    page_icon="🔎",
    layout="wide"
)

# --- Interface do Usuário ---
st.title("🔎 Ferramenta de Busca de Vídeos do YouTube")
st.markdown("Use os filtros na barra lateral para encontrar vídeos e salvá-los em sua Planilha Google.")

# Barra lateral para os inputs
with st.sidebar:
    st.header("⚙️ Filtros de Busca")
    
    termo_busca = st.text_input("Termo de Busca", "Inteligência Artificial para negócios")
    
    dias = st.slider("📅 Buscar nos últimos (dias)", min_value=1, max_value=90, value=7)
    
    duracao_map = {
        "Qualquer uma": "any",
        "Média (4-20 min)": "medium",
        "Longa (+20 min)": "long"
    }
    duracao_selecionada = st.selectbox("⏱️ Duração do Vídeo", options=list(duracao_map.keys()))
    duracao_valor = duracao_map[duracao_selecionada]
    
    idioma = st.text_input("🌐 Idioma do Áudio (código)", "pt")
    
    nome_planilha = st.text_input("📝 Nome da Planilha Google", "Videos YouTube")

    buscar_btn = st.button("🚀 Buscar e Salvar Vídeos", type="primary")

# --- Lógica Principal ---
if buscar_btn:
    if not termo_busca:
        st.warning("Por favor, insira um termo de busca.")
    elif not nome_planilha:
        st.warning("Por favor, insira o nome da sua Planilha Google.")
    else:
        hoje = datetime.now(timezone.utc)
        data_inicio = hoje - timedelta(days=dias)
        
        with st.spinner(f"Buscando vídeos sobre '{termo_busca}'... Isso pode levar um momento."):
            resultados = buscar_videos_youtube(
                query=termo_busca,
                max_results=20,
                published_after=data_inicio.strftime("%Y-%m-%dT%H:%M:%SZ"),
                video_duration=duracao_valor,
                idioma=idioma
            )

        if resultados:
            st.success(f"✅ {len(resultados)} vídeos encontrados!")
            
            with st.spinner("💾 Salvando os dados na sua Planilha Google..."):
                salvar_no_google_sheets(resultados, termo_busca, nome_planilha)
            
            st.info(f"Dados salvos com sucesso na planilha '{nome_planilha}'!")
            
            # Exibe os resultados na tela
            st.markdown("---")
            for video in resultados:
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.image(video['thumbnail_url'])
                with col2:
                    st.subheader(video['title'])
                    views_formatadas = f"{video['views']:,}".replace(",", ".")
                    st.caption(f"Publicado em: {video['published_at'][:10]} | Visualizações: {views_formatadas}")
                    st.markdown(f"[Assistir no YouTube]({video['video_url']})")
                    with st.expander("Ver descrição"):
                        st.write(video['description'] if video['description'] else "Sem descrição.")
        else:
            st.warning("Nenhum vídeo encontrado com os critérios especificados.")