# main.py (Versão para Web)

import streamlit as st
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import (
    format_cell_range,
    set_frozen,
    set_column_width,
    CellFormat,
    TextFormat,
    Color
)
from datetime import datetime

# --- Funções do Backend ---

def buscar_videos_youtube(query, max_results=10, published_after=None, video_duration='any', idioma='pt'):
    """Busca vídeos no YouTube usando a API Key dos Secrets do Streamlit."""
    
    # Lê a API Key dos secrets do Streamlit
    API_KEY = st.secrets.get("youtube", {}).get("api_key")
    if not API_KEY:
        st.error("ERRO: A API Key do YouTube não foi encontrada nos 'Secrets' do Streamlit.")
        return []

    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        search_params = {
            'q': query,
            'part': 'id',
            'maxResults': max_results,
            'type': 'video',
            'relevanceLanguage': idioma,
            'videoDuration': video_duration
        }
        if published_after:
            search_params['publishedAfter'] = published_after

        search_response = Youtube().list(**search_params).execute()
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            return []

        videos_response = youtube.videos().list(
            part='snippet,statistics',
            id=','.join(video_ids)
        ).execute()

        videos = []
        for item in videos_response.get('items', []):
            snippet = item['snippet']
            stats = item['statistics']
            audio_lang = snippet.get('defaultAudioLanguage', '')

            if idioma and not audio_lang.startswith(idioma):
                continue
            
            videos.append({
                'id': item['id'],
                'title': snippet['title'],
                'description': snippet['description'],
                'thumbnail_url': snippet['thumbnails']['high']['url'],
                'video_url': f"https://www.youtube.com/watch?v={item['id']}",
                'views': int(stats.get('viewCount', 0)),
                'published_at': snippet['publishedAt'],
                'audio_lang': audio_lang
            })

        videos.sort(key=lambda x: x['views'], reverse=True)
        return videos

    except Exception as e:
        st.error(f"Ocorreu um erro ao buscar vídeos: {e}")
        return []

def salvar_no_google_sheets(dados, termo_busca, nome_planilha):
    """Salva os dados no Google Sheets usando credenciais dos Secrets do Streamlit."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        google_creds_dict = st.secrets.get("google_sheets_credentials")
        if not google_creds_dict:
            st.error("ERRO: As credenciais do Google Sheets não foram encontradas nos 'Secrets'.")
            return

        creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds_dict, scope)
        client = gspread.authorize(creds)
        planilha = client.open(nome_planilha)

    except Exception as e:
        st.error(f"Erro ao conectar ou abrir a planilha '{nome_planilha}': {e}")
        return

    data_hoje = datetime.now().strftime("%Y-%m-%d")
    nome_aba = f"{termo_busca[:20].strip().lower().replace(' ', '_')}_{data_hoje}"

    try:
        aba_existente = planilha.worksheet(nome_aba)
        planilha.del_worksheet(aba_existente)
    except gspread.WorksheetNotFound:
        pass
    
    aba = planilha.add_worksheet(title=nome_aba, rows="100", cols="10")
    
    headers = ['#', 'Título', 'Visualizações', 'Publicado em', 'URL do Vídeo', 'Descrição', 'URL da Thumbnail', 'Idioma']
    aba.append_row(headers)

    for i, video in enumerate(dados, 1):
        aba.append_row([
            i, video['title'], video['views'], video['published_at'],
            video['video_url'], video['description'][:500],
            video['thumbnail_url'], video['audio_lang']
        ])

    try:
        set_frozen(aba, rows=1)
        format_cell_range(aba, 'A1:H1', CellFormat(
            textFormat=TextFormat(bold=True),
            backgroundColor=Color(0.9, 0.9, 0.9)
        ))
        set_column_width(aba, 'B', 400)
        set_column_width(aba, 'F', 500)

    except Exception as e:
        st.warning(f"Aviso: Erro ao formatar a planilha. Os dados foram salvos, mas sem formatação. Erro: {e}")