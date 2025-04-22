import streamlit as st
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator
import io

# Configurações da página
st.set_page_config(page_title="Dashboard Pacientes", layout="wide")

# Conexão com o banco
def conectar_banco():
    conn = psycopg2.connect(
        host="easypanel.kwautomation.shop",
        port="30420",
        database="projeto_ia",
        user="KEVIN",
        password="kevin123",
        sslmode="disable"
    )
    return conn

def carregar_dados():
    conexao = conectar_banco()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome, cpf, genero, suicidio_historico, familia_historico, substancias_uso, predicao FROM requisicoes")
    resultados = cursor.fetchall()
    colunas = ["Nome", "CPF", "Gênero", "Histórico de Suicídio", "Histórico Familiar", "Uso de Substância", "Predição"]
    df = pd.DataFrame(resultados, columns=colunas)
    conexao.close()
    return df

# Estilos visuais do Streamlit
st.markdown("""
    <style>
        body {
            background-color: #0E1117;
        }
        .block-container {
            background-color: #0E1117;
            padding-top: 0.1rem; 
            padding-bottom: 1rem;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        section[data-testid="stSidebar"] {
            background-color: #56447A;
        }
        section[data-testid="stSidebar"] .css-1cpxqw2 {
            color: #ffffff;
        }
    </style>
""", unsafe_allow_html=True)


# Estilo dos cards 
def metric_card(titulo, valor, subtitulo):
    st.markdown(f"""
        <div style="background-color: #ffffff; padding: 6px; border-radius: 8px; 
                    text-align: center; box-shadow: 1px 1px 4px rgba(0,0,0,0.1); 
                    font-size: 10px;">
            <h5 style="color: #6A1B9A; margin: 0;">{titulo}</h5>
            <h3 style="color: #8E24AA; margin: 5px 0;">{valor}</h3>
            <p style="color: #A66BBE; margin: 0; font-size: 16px;">{subtitulo}</p> 
        </div>
    """, unsafe_allow_html=True)

dados = carregar_dados()

# Filtros laterais
generos = sorted(dados["Gênero"].dropna().unique().tolist())
genero_filtrado = st.sidebar.selectbox("Gênero:", ["Todos"] + generos)

suicidio_historico = dados["Histórico de Suicídio"].dropna().unique()
suicidio_filtrado = st.sidebar.selectbox("Histórico de Suicídio:", ["Todos"] + list(suicidio_historico))

familia_historico = dados["Histórico Familiar"].dropna().unique()
familia_filtrado = st.sidebar.selectbox("Histórico Familiar:", ["Todos"] + list(familia_historico))

substancias_uso = dados["Uso de Substância"].dropna().unique()
substancias_filtrado = st.sidebar.selectbox("Uso de Substância:", ["Todos"] + list(substancias_uso))

predicoes_valores = dados["Predição"].dropna().astype(str).unique().tolist()
predicao_filtrada = st.sidebar.selectbox("Predição (Risco Detectado):", ["Todos"] + predicoes_valores)

cpf_pesquisar = st.sidebar.text_input("Pesquisar CPF (XXX.XXX.XXX-XX):")

# Botão de download do relatório Excel
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Exportar Relatório")

dados_para_excel = carregar_dados()  # Dados sem filtros
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    dados_para_excel.to_excel(writer, sheet_name='Pacientes', index=False)
    writer.close()
    buffer.seek(0)

st.sidebar.download_button(
    label="📊 Baixar Excel",
    data=buffer,
    file_name="relatorio_pacientes.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Aplicar filtros
if genero_filtrado != "Todos":
    dados = dados[dados["Gênero"] == genero_filtrado]
if suicidio_filtrado != "Todos":
    dados = dados[dados["Histórico de Suicídio"] == suicidio_filtrado]
if familia_filtrado != "Todos":
    dados = dados[dados["Histórico Familiar"] == familia_filtrado]
if substancias_filtrado != "Todos":
    dados = dados[dados["Uso de Substância"] == substancias_filtrado]
if predicao_filtrada != "Todos":
    dados = dados[dados["Predição"].astype(str) == predicao_filtrada]

# Para contar os casos positivos de "Uso de Substância"
uso_substancia_positivo = dados[dados["Uso de Substância"] == "sim"].shape[0]

# Se CPF for pesquisado
if cpf_pesquisar:
    paciente_encontrado = dados[dados["CPF"] == cpf_pesquisar]
    if not paciente_encontrado.empty:
        st.subheader("🔎 Paciente Encontrado")
        st.dataframe(paciente_encontrado, height=150)
    else:
        st.warning("Nenhum paciente encontrado com esse CPF.")
else:
    total_pacientes = len(dados)
    esquizofrenia_predicao_positiva = dados[dados["Predição"].astype(str) == "1"].shape[0]
    suicidio_positivo = dados[dados["Histórico de Suicídio"] == "Sim"].shape[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Pacientes", total_pacientes, "Total filtrado")
    with col2:
        metric_card("Predições Positivas", esquizofrenia_predicao_positiva, "Para Esquizofrenia")
    with col3:
        metric_card("Uso de Substância", uso_substancia_positivo, "Casos Positivos")

    st.markdown("<hr style='border: 1px solid #56447A; margin-top: 30px; margin-bottom: 30px;'>", unsafe_allow_html=True)


    # Tabela 
    st.subheader("📋 Lista de Pacientes")
    st.dataframe(dados, use_container_width=True, height=200)

    st.markdown("<hr style='border: 1px solid #56447A; margin-top: 30px; margin-bottom: 30px;'>", unsafe_allow_html=True)


    # Gráficos
    genero_count = dados["Gênero"].value_counts()
    suicidio_count = dados["Histórico de Suicídio"].value_counts()
    substancias_count = dados["Uso de Substância"].value_counts()
    predicao_count = dados["Predição"].value_counts()

    # Gêneros
    fig1, ax1 = plt.subplots(figsize=(2.5, 2))
    sns.barplot(
        x=genero_count.index,
        y=genero_count.values,
        ax=ax1,
        palette="Purples"
    )
    ax1.set_title("Gêneros", fontsize=8, color="#6A1B9A")
    ax1.set_xlabel("")
    ax1.set_ylabel("Quantidade", fontsize=6)
    ax1.tick_params(axis='x', labelrotation=30, labelsize=6)
    ax1.tick_params(axis='y', labelsize=6)
    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Histórico de Suicídio (Pizza)
    fig2, ax2 = plt.subplots(figsize=(2.5, 1.1))
    cores_roxas = sns.color_palette("Purples", n_colors=len(suicidio_count))

    ax2.pie(
        suicidio_count,
        labels=suicidio_count.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=cores_roxas,
        textprops={'fontsize': 4}
    )
    ax2.set_title("Histórico de Suicídio", fontsize=8, color="#6A1B9A")

    # Uso de Substância (Barras laterais)
    fig3, ax3 = plt.subplots(figsize=(2.5, 1.5))
    sns.barplot(
        y=substancias_count.index,
        x=substancias_count.values,
        ax=ax3,
        palette="Purples"
    )
    ax3.set_title("Uso de Substância", fontsize=8, color="#6A1B9A")
    ax3.set_xlabel("Quantidade", fontsize=6)
    ax3.set_ylabel("")
    ax3.tick_params(axis='y', labelsize=6)
    ax3.tick_params(axis='x', labelsize=6)
    ax3.xaxis.set_major_locator(MaxNLocator(integer=True))  

    # Predição (Barras verticais)
    predicao_labels = pd.Series(predicao_count.index).astype(int).map({1: "1 (Sim)", 0: "0 (Não)"})
    fig4, ax4 = plt.subplots(figsize=(2.5, 1.5))
    sns.barplot(
        x=predicao_labels,
        y=predicao_count.values,
        palette="Purples",
        ax=ax4
    )
    ax4.set_title("Predição (Risco)", fontsize=8, color="#6A1B9A")
    ax4.set_xlabel("Predição", fontsize=6)
    ax4.set_ylabel("Quantidade", fontsize=6)
    ax4.tick_params(axis='x', labelsize=6)
    ax4.tick_params(axis='y', labelsize=6)
    ax4.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    # Exibição dos gráficos
    col4, col5 = st.columns(2)
    with col4:
        st.pyplot(fig1)
    with col5:
        st.pyplot(fig2)

    col6, col7 = st.columns(2)
    with col6:
        st.pyplot(fig3)
    with col7:
        st.pyplot(fig4)

# Botão de sair
st.sidebar.markdown("""
    <hr style="margin-top: 20px; margin-bottom: 10px;">
    <a href="https://neurotrack.kwautomation.shop/" target="_self" style="text-decoration: none;">
        <div style="background-color: #D32F2F; color: white; padding: 10px; border-radius: 5px; 
                    text-align: center; font-weight: bold; font-size: 14px;">
            🚪 Sair
        </div>
    </a>
""", unsafe_allow_html=True)