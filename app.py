import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import plotly.express as px
import pytesseract
from PIL import Image
import holidays
import sweetviz as sv
import streamlit.components.v1 as components


# Configuração do pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
import os
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"

# Conexão com o MongoDB
mongo_url = "mongodb+srv://renataturriararipe:HouseCar26@treino.rpvp5.mongodb.net/"
client = MongoClient(mongo_url)
db = client['dashboard_db']
treinos_collection = db['treinos']

# Função para carregar treinos
def carregar_treinos():
    dados = list(treinos_collection.find({}, {"_id": 0}))
    return pd.DataFrame(dados)

# Função para processar a imagem e extrair dados
def processar_imagem(imagem):
    texto = pytesseract.image_to_string(imagem, lang="por")  # OCR em português
    # Exemplo de parsing dos dados extraídos do texto
    dados = {
        "bpm_medio": None,
        "bpm_max": None,
        "calorias": None,
        "tempo_total": None,
    }

    # Tentativa de extrair dados do texto com base em palavras-chave
    for linha in texto.splitlines():
        if "Média de frequência cardíaca" in linha:
            dados["bpm_medio"] = int(linha.split()[0])
        elif "BPM máximo" in linha:
            dados["bpm_max"] = int(linha.split()[0])
        elif "Queimou" in linha:
            dados["calorias"] = int(linha.split()[0])
        elif "Tempo total" in linha:
            tempo = linha.split()[0].split(":")
            dados["tempo_total"] = int(tempo[0]) * 60 + int(tempo[1])  # Converter HH:MM para minutos

    return dados

# Título da Aplicação
st.title("Dashboard de Treinos - Streamlit")

# Divisão da Interface com abas
abas = st.tabs(["Adicionar Treino", "Análise de Treinos", "Gráficos de Progresso", "Meta Anual e Assiduidade", "Medidas Corporais"])

def calcular_dias_uteis(data_inicial, data_final):
    """
    Calcula o número de dias úteis entre duas datas, excluindo fins de semana e feriados no Brasil.
    """
    # Lista de feriados no Brasil
    feriados_brasil = holidays.BR(years=range(data_inicial.year, data_final.year + 1), subdiv="SP")
    
    # Cria um range de dias úteis (exclui fins de semana)
    dias_uteis = pd.date_range(start=data_inicial, end=data_final, freq='B')
    
    # Remove feriados
    dias_uteis = [dia for dia in dias_uteis if dia not in feriados_brasil]
    
    return len(dias_uteis)

# Aba 1: Formulário para adicionar treinos
with abas[0]:
    st.header("📋 Adicionar Novo Treino")

    # Upload de imagem
    imagem = st.file_uploader("Carregar Relatório do Relógio (Imagem)", type=["jpg", "jpeg", "png"])
    dados_extraidos = {}

    if imagem:
        imagem_pil = Image.open(imagem)
        st.image(imagem_pil, caption="Imagem Carregada", use_column_width=True)
        dados_extraidos = processar_imagem(imagem_pil)
        st.success("Dados extraídos da imagem com sucesso!")

    # Preencher os campos automaticamente, se os dados foram extraídos
    with st.form("form_treino"):
        data = st.date_input("Data do treino", value=datetime.now())
        tipo_treino = st.selectbox(
            "Tipo de Treino",
            ["Posterior, Glúteos e Adutores", "Quadríceps, Glúteos e Panturrilhas", "Peito, Ombro e Tríceps", "Costas e Bíceps", "Core + HIIT", "Aeróbico", "Outro"]
        )
        duracao = st.number_input("Duração do Treino (min)", min_value=0, step=1, value=dados_extraidos.get("tempo_total", 0))
        calorias = st.number_input("Calorias Queimadas", min_value=0, step=1, value=dados_extraidos.get("calorias", 0))
        bpm_medio = st.number_input("Batimento Médio (bpm)", min_value=0, step=1, value=dados_extraidos.get("bpm_medio", 0))
        bpm_max = st.number_input("Batimento Máximo (bpm)", min_value=0, step=1, value=dados_extraidos.get("bpm_max", 0))
        zona_leve = st.number_input("Zona Leve (min)", min_value=0, step=1)
        zona_intensa = st.number_input("Zona Intensa (min)", min_value=0, step=1)
        zona_aerobica = st.number_input("Zona Aeróbica (min)", min_value=0, step=1)
        zona_anaerobica = st.number_input("Zona Anaeróbica (min)", min_value=0, step=1)
        zona_maxvo = st.number_input("Zona Max. VO2 (min)", min_value=0, step=1)
        mobilidade = st.number_input("Mobilidade (min)", min_value=0, step=1)
        aerobico = st.number_input("Aeróbico (min)", min_value=0, step=1)
        comentarios = st.text_area("Comentários sobre o treino")

        # Botão de submissão
        submit_button = st.form_submit_button(label="Salvar Treino")

        if submit_button:
            novo_treino = {
                "Data": data.strftime("%d/%m/%Y"),
                "Tipo de Treino": tipo_treino,
                "Tempo Total (min)": duracao,
                "Calorias Queimadas": calorias,
                "Batimento Médio (bpm)": bpm_medio,
                "Batimento Máximo (bpm)": bpm_max,
                "Zona Leve (min)": zona_leve,
                "Zona Intensa (min)": zona_intensa,
                "Zona Aeróbica (min)": zona_aerobica,
                "Zona Anaeróbica (min)": zona_anaerobica,
                "Zona Max. VO2 (min)": zona_maxvo,
                "Mobilidade (min)": mobilidade,
                "Aeróbico (min)": aerobico,
                "Comentários": comentarios
            }
            treinos_collection.insert_one(novo_treino)
            st.success("Treino salvo com sucesso!")

# Aba 2: Exibição de dados
with abas[1]:
    st.header("📊 Análise de Treinos")
    df_treinos = carregar_treinos()

    if not df_treinos.empty:
        st.dataframe(df_treinos)

        # Estatísticas gerais
        st.subheader("📈 Estatísticas Gerais")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total de Treinos", len(df_treinos))

        with col2:
            st.metric("Tempo Total de Treino (min)", df_treinos["Tempo Total (min)"].sum())
            st.metric("Tempo Médio de Treino (min)", df_treinos["Tempo Total (min)"].mean().astype(int))

        with col3:
            st.metric("Total de Calorias Queimadas", df_treinos["Calorias Queimadas"].sum())
            st.metric("Média de Calorias Gastas por Treino", df_treinos["Calorias Queimadas"].mean().astype(int))
        
    else:
        st.warning("Nenhum treino encontrado. Adicione novos treinos na aba anterior.")

# Aba 3: Gráficos
with abas[2]:
    st.header("📅 Gráficos de Progresso")
    if not df_treinos.empty:
        # Calorias acumuladas por dia
        df_treinos["Data"] = pd.to_datetime(df_treinos["Data"], format="%d/%m/%Y")
        calorias_acumuladas = df_treinos.groupby(df_treinos["Data"].dt.date)["Calorias Queimadas"].sum().reset_index()
        calorias_acumuladas.columns = ["Data", "Calorias Queimadas"]
        fig_calorias = px.bar(calorias_acumuladas, x="Data", y="Calorias Queimadas", title="Calorias Acumuladas")
        st.plotly_chart(fig_calorias, use_container_width=True)

        # Tempo de treino acumulado por dia
        tempo_acumulado = df_treinos.groupby(df_treinos["Data"].dt.date)["Tempo Total (min)"].sum().reset_index()
        tempo_acumulado.columns = ["Data", "Tempo Total (min)"]
        fig_tempo = px.bar(tempo_acumulado, x="Data", y="Tempo Total (min)", title="Tempo Total Acumulado")
        st.plotly_chart(fig_tempo, use_container_width=True)

    else:
        st.warning("Nenhum dado disponível para gerar gráficos.")


# Função para carregar os dados
    def carregar_treinos():
        dados = list(treinos_collection.find({}, {"_id": 0}))
        return pd.DataFrame(dados)

# Carregar os dados
    df_treinos = carregar_treinos()

# Analisar os dados com Sweetviz
   # if not df_treinos.empty:
    #    relatorio = sv.analyze(df_treinos)
    #    relatorio.show_html("relatorio_treinos.html", open_browser=False)

    # Exibir no Streamlit
     #   st.header("📊 Relatório Sweetviz")
     #   HtmlFile = open("relatorio_treinos.html", 'r', encoding='utf-8')
     #   source_code = HtmlFile.read() 
     #   components.html(source_code, height=800, scrolling=True)
    #else:
     #   st.warning("Nenhum dado disponível para análise.")

# Aba 4: Meta Anual e Indicador de Assiduidade
with abas[3]:
    st.header("📊 Meta Anual e Indicador de Assiduidade")

    # Carregar dados do MongoDB
    df_treinos = carregar_treinos()
    if not df_treinos.empty:
        # Garantir que as datas estejam no formato correto
        df_treinos["Data"] = pd.to_datetime(df_treinos["Data"], format="%d/%m/%Y")

        # Dados gerais
        hoje = datetime.now()
        dias_uteis_ano = calcular_dias_uteis(datetime(hoje.year, 1, 1), hoje)
        dias_uteis_mes = calcular_dias_uteis(datetime(hoje.year, hoje.month, 1), hoje)

        dias_treinados_ano = df_treinos["Data"].nunique()
        dias_treinados_mes = df_treinos[df_treinos["Data"].dt.month == hoje.month]["Data"].nunique()

        assiduidade_anual = (dias_treinados_ano / dias_uteis_ano) * 100
        assiduidade_mensal = (dias_treinados_mes / dias_uteis_mes) * 100

        # Criar layout com colunas para organização
        st.subheader("📈 Indicadores de Assiduidade")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Dias úteis no ano", dias_uteis_ano)
            st.metric("Dias treinados no ano", dias_treinados_ano)
            st.metric("Assiduidade Anual (%)", f"{assiduidade_anual:.2f}")

        with col2:
            st.metric("Dias úteis no mês", dias_uteis_mes)
            st.metric("Dias treinados no mês", dias_treinados_mes)
            st.metric("Assiduidade Mensal (%)", f"{assiduidade_mensal:.2f}")

        # Gráfico Progresso Anual
        st.subheader("📅 Progresso Anual")
        progresso_anual = df_treinos.groupby(df_treinos["Data"].dt.month).size().reset_index(name="Dias Treinados")
        progresso_anual.columns = ["Mês", "Dias Treinados"]
        progresso_anual["Mês"] = progresso_anual["Mês"].apply(lambda x: datetime(2025, x, 1).strftime("%B"))
        fig_progresso_anual = px.bar(progresso_anual, x="Mês", y="Dias Treinados", title="Progresso Anual")
        st.plotly_chart(fig_progresso_anual, use_container_width=True)

    else:
        st.warning("Nenhum dado disponível para a meta anual.")

# Função para carregar medidas corporais
def carregar_medidas():
    medidas_collection = db['medidas']  # Certifique-se de que a coleção 'medidas' existe no MongoDB
    dados = list(medidas_collection.find({}, {"_id": 0}))
    return pd.DataFrame(dados)

# Aba 5: Medidas Corporais
with abas[4]:  # Certifique-se de que esta seja a 5ª aba adicionada
    st.header("📏 Medidas Corporais")

    # Carregar dados de medidas corporais
    df_medidas = carregar_medidas()

    if not df_medidas.empty:
        st.dataframe(df_medidas)

        # Seleção de medidas para exibição no gráfico
        st.subheader("📊 Gráfico Temporal de Medidas")
        medidas_disponiveis = df_medidas.columns.drop(["data", "observacoes", "id_medida"])  # Exclui colunas irrelevantes
        medidas_selecionadas = st.multiselect(
            "Selecione as Medidas para Exibir:",
            options=medidas_disponiveis,
            default=medidas_disponiveis[:2],  # Exibe as duas primeiras medidas por padrão
        )

        if medidas_selecionadas:
            # Criar gráfico temporal com base nas medidas selecionadas
            fig_medidas = px.line(
                df_medidas,
                x="data",
                y=medidas_selecionadas,
                title="Evolução das Medidas ao Longo do Tempo",
                labels={"value": "Valor", "variable": "Medida"},
                text="value"  # Exibe os valores como texto
            )
            fig_medidas.update_traces(
                textposition="top center"  # Posiciona o texto acima dos pontos
            )
            st.plotly_chart(fig_medidas, use_container_width=True)
        else:
            st.warning("Selecione ao menos uma medida para exibir no gráfico.")
    else:
        st.warning("Nenhuma medida corporal encontrada no banco de dados.")


# Executar a aplicação
