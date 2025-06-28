#Import libraries
import streamlit as st
import pandas as pd
import json
import gdown #Use gdown to Access the File
import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import gc
import os

# Check whether the JSON files have been loaded into the python application
#if 'df_Vagas' not in globals() and 'df_Applicants' not in globals():
if 'df_Vagas' not in st.session_state or 'df_Applicants' not in st.session_state:
    # #Imports JSON files from my personal Google Drive (files made public)
    # # Replace with your own FILE_ID
    # file_Prospects  = '1sh88eHjyIp0wXtcRIFozgN064VGOOxEs'
    file_Applicants = '17859ae_Ki5CImI9-1lhJ335GMDW0f2Qr'
    file_Vagas      = '1YKM7yDTzjHJVf82l2RxEx-SuLxFxCxrl'

    # # Download the JSON files
    # gdown.download(f'https://drive.google.com/uc?export=download&id={file_Prospects}', 'prospects.json', quiet=False)
    gdown.download(f'https://drive.google.com/uc?export=download&id={file_Applicants}', 'applicants.json', quiet=False)
    gdown.download(f'https://drive.google.com/uc?export=download&id={file_Vagas}', 'vagas.json', quiet=False)

    # #Load the JSON File into Python
    # with open('prospects.json', 'r') as prospects_file:
    #     data_Prospects = json.load(prospects_file)

    with open('applicants.json', 'r') as applicants_file:
        data_Applicants = json.load(applicants_file)

    with open('vagas.json', 'r') as vagas_file:
        data_Vagas = json.load(vagas_file)


    # # Convert the JSON so that each prospect candidate is represented as a separate row in the DataFrame
    # # -----------------------
    # #prospects.JSON file
    # # -----------------------
    # records = []

    # for prof_id, profile_info in data_Prospects.items():
    #     titulo = profile_info.get("titulo")
    #     modalidade = profile_info.get("modalidade")

    #     for prospect in profile_info.get("prospects", []):
    #         record = {
    #             "id_prospect": prof_id,
    #             "titulo": titulo,
    #             "modalidade": modalidade,
    #             "nome_candidato": prospect.get("nome"),
    #             "codigo_candidato": prospect.get("codigo"),
    #             "situacao_candidado": prospect.get("situacao_candidado"),
    #             "data_candidatura": prospect.get("data_candidatura"),
    #             "ultima_atualizacao": prospect.get("ultima_atualizacao"),
    #             "comentario": prospect.get("comentario"),
    #             "recrutador": prospect.get("recrutador")
    #         }
    #         records.append(record)

    # # Convert to DataFrame
    # df_Prospects = pd.DataFrame(records)


    # -----------------------
    #applicants.JSON file
    # -----------------------
    records = []

    for prof_id, profile_info in data_Applicants.items():
        record = {
            "id_applicant": prof_id
        }

        # Flatten sections
        for section_name, section_data in profile_info.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    record[f"{section_name}__{key}"] = value
            else:
                # Just in case any sections are not dicts (e.g., cv_pt or cv_en directly under profile)
                record[section_name] = section_data

        records.append(record)

    # Convert to DataFrame
    #df_Applicants = pd.DataFrame(records)
    st.session_state.df_Applicants = pd.DataFrame(records)

    #test

    # -----------------------
    #vagas.JSON file
    # -----------------------
    records = []

    for prof_id, profile_info in data_Vagas.items():
        record = {
            "id_vaga": prof_id
        }

        # Flatten sections
        for section_name, section_data in profile_info.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    record[f"{section_name}__{key}"] = value
            else:
                record[section_name] = section_data

        records.append(record)

    # Convert to DataFrame
    #df_Vagas = pd.DataFrame(records)
    st.session_state.df_Vagas = pd.DataFrame(records)


    #Release memory used
    # Clear variables
    del data_Vagas
    del data_Applicants
    # Force garbage collection
    gc.collect()

    
df_Vagas = st.session_state.df_Vagas
df_Applicants = st.session_state.df_Applicants

# Count NaN or empty values per column
empty_counts = (df_Vagas.isnull() | (df_Vagas == '')).sum()

# Identify columns with more than 13.000 missing/empty values
cols_to_drop = empty_counts[empty_counts > 13000].index

# Drop them from the DataFrame
df_Vagas.drop(columns=cols_to_drop, inplace=True)

# Convert date fields to datetime
df_Vagas['informacoes_basicas__data_requicisao'] = pd.to_datetime(df_Vagas['informacoes_basicas__data_requicisao'], format='%d-%m-%Y', errors='coerce' )
df_Vagas['informacoes_basicas__data_inicial'] = pd.to_datetime(df_Vagas['informacoes_basicas__data_inicial'], format='%d-%m-%Y', errors='coerce' )
df_Vagas['informacoes_basicas__data_final'] = pd.to_datetime(df_Vagas['informacoes_basicas__data_final'], format='%d-%m-%Y', errors='coerce' )

#Montando a estrutura do dashboard
# -----------------------------
# Título e introdução
# -----------------------------
st.set_page_config(page_title="Sistema de Recomendação de Talentos por Vaga", layout="wide")

st.title("Dashboard de Matching entre Vagas e Candidatos")
st.subheader("Selecione uma vaga na aba filtros para visualizar os candidatos mais compatíveis")

# -----------------------------
# Sidebar - Filtros e seleção
# -----------------------------
st.sidebar.header("Selecione a vaga desejada")

#Lista de meses existentes na base de vagas
# Criar nova coluna no formato 'MMM.yyyy'
df_Vagas['mes_ano'] = df_Vagas['informacoes_basicas__data_requicisao'].dt.strftime('%b.%Y')

# Converter para datetime temporariamente (formato: %b.%Y → 'Apr.2019')
lista_meses_ordenada = sorted(
    df_Vagas['mes_ano'].dropna().unique(),
    key=lambda x: pd.to_datetime(x, format='%b.%Y')
)
# Mês.Ano Filtro lateral
mth_selecionado = st.sidebar.selectbox("Mês.Ano:", lista_meses_ordenada)

# Exemplo de seleção de vaga - Lista de vagas
#lista_vagas = sorted(df_Vagas['informacoes_basicas__titulo_vaga'])
#vaga_selecionada = st.sidebar.selectbox("Mês.Ano:", lista_vagas)

#Ações quando o um valor no filtro for selecionado
# Filtrar o dataframe pelo mês selecionado
df_filtrado = df_Vagas[df_Vagas['mes_ano'] == mth_selecionado]

# Gerar lista de vagas com base no mês selecionado
lista_vagas = sorted(df_filtrado['informacoes_basicas__titulo_vaga'].dropna().unique())

# "Titulo da vaga" Filtro lateral
vaga_selecionada = st.sidebar.selectbox("Título da vaga:", lista_vagas)


# -----------------------------
# Análise dos possívels matches da vaga de candidatos da base Applicants 
# -----------------------------
#Load and Preprocess Your CV Data

# Basic text cleaning
def clean_text(text):
    text = re.sub(r'\n', ' ', text)  # Remove line breaks
    text = re.sub(r'[^a-zA-Z0-9À-ÿ ]', '', text)  # Keep accented characters
    text = text.lower()  # Lowercase
    # Normalize accented characters to plain ASCII (e.g., é → e)
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')

    return text

df_Vagas['comparison_info'] = df_Vagas['perfil_vaga__competencia_tecnicas_e_comportamentais']
#Clean special characters
df_Vagas['comparison_info'] = df_Vagas['comparison_info'].apply(clean_text)

# Example: compare first job in df_Vagas against all applicants
job_description = df_Vagas['comparison_info'].iloc[0]

# Combine the job description and all CVs into one list
texts = [job_description] + df_Applicants['cv_pt'].fillna('').tolist()

# Convert to TF-IDF vectors
vectorizer = TfidfVectorizer(stop_words=None)
tfidf_matrix = vectorizer.fit_transform(texts)

# Compute cosine similarity between job and each CV
similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

# Add results to df_Applicants
df_Applicants['match_score'] = similarities

# Sort to get best-matching candidates
top_matches = df_Applicants.sort_values(by='match_score', ascending=False)

# Display top N
# print(top_matches[['cv_pt', 'match_score']].head(5))

# -----------------------------
# Filtro por estado (local da vaga)
# -----------------------------
list_local = sorted(df_Applicants['local'].dropna().unique())
candidato_local_selecionado = st.sidebar.selectbox("Filtrar por estado:", list_local)
opcoes = st.multiselect(list_local)

# Filtrar vagas pelo estado selecionado
top_matches_filtrado = top_matches[top_matches['local'] == candidato_local_selecionado]


# -----------------------------
# Exibição dos candidatos compatíveis
# -----------------------------
st.markdown(f"### Candidatos compatíveis com a vaga: {vaga_selecionada}")
st.markdown("### DataFrames currently in `st.session_state`")

for key, value in st.session_state.items():
    if isinstance(value, pd.DataFrame):
        st.markdown(f"#### `{key}`")
        st.dataframe(value)

st.dataframe(top_matches_filtrado[['cv_pt', 'match_score']], use_container_width=True)


# st.set_page_config(
#     page_title = 'PAINEL DE AÇÕES DA B3',
#     layout = 'wide'
# )

# st.header("**PAINEL DE PREÇO DE FECHAMENTO E DIVIDENDOS DE AÇÕES DA B3**")

# st.markdown("**PAINEL DE PREÇO DE FECHAMENTO E DIVIDENDfffOS DE AÇÕES DA B3**")


# ticker = st.text_input('Digite o ticket da ação', 'BBAS3')
# empresa = yf.Ticker(f"{ticker}.SA")

# tickerDF = empresa.history( period  = "1d",
#                             start   = "2019-01-01",
#                             end     = "2025-01-20"
# )

# col1, col2, col3 = st.columns([1, 1, 1])

# with col1:
#     st.write(f"**Empresa:**  {empresa.info['longName']}")
# with col2:
#     st.write(f"**Mercado:** R$ {empresa.info['industry']}")
# with col3:
#     st.write(f"**Preço Atual:** R$ {empresa.info['currentPrice']}")

# st.line_chart(tickerDF.Close)
# st.bar_chart(tickerDF.Dividends)