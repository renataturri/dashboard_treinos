import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import plotly.express as px
import pytesseract
from PIL import Image
import holidays
import os
import sweetviz as sv
import streamlit.components.v1 as components
import requests


# Configuração do pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"

# Configuração de página
st.set_page_config(
    page_title="Dashboard de Treinos",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título do app
st.title("Dashboard de Treinos")

# Conexão com o MongoDB
mongo_url = os.getenv("MONGO_URL") #Para o Deploy
client = MongoClient(mongo_url)
db = client['dashboard_db']
treinos_collection = db['treinos']
medidas_collection = db['medidas']
exercicios_collection = db['exercicios']
registros_exercicios_collection = db['registros_exercicios']
condicoes_treino_collection = db['condicoes_treino']

# Funções para carregar dados
# Funções para carregar dados
def carregar_treinos():
    dados = list(treinos_collection.find({}, {"_id": 0}))
    return pd.DataFrame(dados)

def carregar_medidas():
    dados = list(medidas_collection.find({}, {"_id": 0}))
    return pd.DataFrame(dados)

def carregar_exercicios():
    dados = list(exercicios_collection.find({}))
    return pd.DataFrame(dados)

# Função para calcular dias úteis
def calcular_dias_uteis(data_inicial, data_final):
    feriados_brasil = holidays.BR(years=range(data_inicial.year, data_final.year + 1), subdiv="SP")
    dias_uteis = pd.date_range(start=data_inicial, end=data_final, freq='B')
    return len([dia for dia in dias_uteis if dia not in feriados_brasil])

# Função para processar imagem
def processar_imagem(imagem):
    texto = pytesseract.image_to_string(imagem, lang="por")
    dados = {
        "bpm_medio": None,
        "bpm_max": None,
        "calorias": None,
        "tempo_total": None,
    }
    for linha in texto.splitlines():
        if "Média de frequência cardíaca" in linha:
            dados["bpm_medio"] = int(linha.split()[0])
        elif "BPM máximo" in linha:
            dados["bpm_max"] = int(linha.split()[0])
        elif "Queimou" in linha:
            dados["calorias"] = int(linha.split()[0])
        elif "Tempo total" in linha:
            tempo = linha.split()[0].split(":")
            dados["tempo_total"] = int(tempo[0]) * 60 + int(tempo[1])
    return dados

# Função para carregar as condições de treino
def carregar_condicoes():
    dados = list(condicoes_treino_collection.find({}))  # Certifique-se de que a coleção existe
    return pd.DataFrame(dados)

# Função para carregar registros de exercícios
def carregar_registros_exercicios():
    """
    Carrega os registros de exercícios da coleção 'registros_exercicios' no MongoDB.
    """
    dados = list(registros_exercicios_collection.find({}, {"_id": 0}))
    return dados

def carregar_medidas():
    medidas_collection = db['medidas']  # Certifique-se de que a coleção 'medidas' existe no MongoDB
    dados = list(medidas_collection.find({}, {"_id": 0}))
    return pd.DataFrame(dados)

# Define DE:PARA para tipos de treino
de_para = {
    "Posterior, Glúteos e Adutores": "Treino A - Posterior",
    "Quadríceps, Glúteos e Panturrilhas": "Treino B - Quadríceps",
    "Peito, Ombro e Tríceps": "Treino C - Superior Empurrar",
    "Costas e Bíceps": "Treino D - Superior Puxar",
    "Core + HIIT": "Treino E - Core e HIIT",
    "Aeróbico": "Treino F - Aeróbico"
}

# Dashboard Tabs
abas = st.tabs([
    "Adicionar Treino", "Registrar Exercícios", "Adicionar Medidas", 
    "Análise de Treinos", "Meta Anual e Assiduidade",
    "Medidas Corporais", "Indicadores de Treinos"
])

# Aba 1: Adicionar Treino
with abas[0]:
    st.header("📋 Adicionar Novo Treino")
    imagem = st.file_uploader("Carregar Relatório do Relógio (Imagem)", type=["jpg", "jpeg", "png"])
    dados_extraidos = {}
    if imagem:
        imagem_pil = Image.open(imagem)
        st.image(imagem_pil, caption="Imagem Carregada", use_container_width=True)
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

# Aba 2: Registrar Exercícios
# Registrar Exercícios
with abas[1]:
    st.header("🏋️‍♀️ Registrar Exercícios")
    st.subheader("Selecione o Treino e Registre os Detalhes")

    # Carrega os exercícios do banco de dados
    df_exercicios = carregar_exercicios()

    if not df_exercicios.empty:
        # Ajuste no dropdown para usar os valores corretos
        tipo_treino = st.selectbox(
            "Selecione o Tipo de Treino",
            options=[
                "Posterior e Glúteos",
                "Quadriceps",
                "Superiores empurrar",
                "Superiores puxar",
                "Core e HIIT"
            ]
        )

        # Filtrar exercícios com base no dia_do_treino
        exercicios_filtrados = df_exercicios[df_exercicios["dia_do_treino"] == tipo_treino]

        if not exercicios_filtrados.empty:
            st.write(f"Exercícios para o treino: {tipo_treino}")
            st.dataframe(exercicios_filtrados)
            with st.form("form_exercicios"):
                # Entrada para selecionar a data do treino
                data_treino = st.date_input("Data do Treino", value=datetime.now())
                
                registros = []
                for _, row in exercicios_filtrados.iterrows():
                    repeticoes = st.number_input(f"Repetições - {row['nome']}", min_value=0, step=1)
                    peso = st.number_input(f"Peso (kg) - {row['nome']}", min_value=0.0, step=0.1)
                    registros.append({
                        "Exercício": row["nome"], 
                        "Repetições": repeticoes, 
                        "Peso (kg)": peso,
                        "Data": data_treino.strftime("%Y-%m-%d")  # Formatar a data como string
                    })

                submit_exercicio = st.form_submit_button("Salvar Exercícios")
                if submit_exercicio:
                    registros_exercicios_collection.insert_one({
                        "Treino": tipo_treino,
                        "Data do Registro": data_treino.strftime("%Y-%m-%d"),
                        "Detalhes": registros
                    })
                    st.success("Exercícios registrados com sucesso!")
        else:
            st.warning(f"Nenhum exercício encontrado para o treino selecionado: {tipo_treino}.")
    else:
        st.warning("Nenhum exercício disponível no banco de dados.")

# Aba 3: Adicionar Medidas Corporais
with abas[2]:
    st.header("📏 Adicionar Medidas Corporais e Condições do Treino")
    with st.form("form_medidas"):
        # Medidas Corporais
        st.subheader("📐 Medidas Corporais")
        data = st.date_input("Data", value=datetime.now())
        peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
        torax = st.number_input("Tórax (cm)", min_value=0.0, step=0.1)
        cintura = st.number_input("Cintura (cm)", min_value=0.0, step=0.1)
        abdomen = st.number_input("Abdômen (cm)", min_value=0.0, step=0.1)
        quadril = st.number_input("Quadril (cm)", min_value=0.0, step=0.1)
        braco_direito = st.number_input("Braço Direito (cm)", min_value=0.0, step=0.1)
        braco_esquerdo = st.number_input("Braço Esquerdo (cm)", min_value=0.0, step=0.1)
        coxa_direita = st.number_input("Coxa Direita (cm)", min_value=0.0, step=0.1)
        coxa_esquerda = st.number_input("Coxa Esquerda (cm)", min_value=0.0, step=0.1)
        panturrilha_direita = st.number_input("Panturrilha Direita (cm)", min_value=0.0, step=0.1)
        panturrilha_esquerda = st.number_input("Panturrilha Esquerda (cm)", min_value=0.0, step=0.1)
        observacoes = st.text_area("Observações sobre as medidas")

        # Condições do Treino
        st.subheader("💪 Condições do Treino")
        tsb = st.number_input("TSB (Forma de Treinamento)", min_value=0.0, step=0.1)
        fadiga = st.number_input("Fadiga (ATL)", min_value=0.0, step=0.1)
        condicao_fisica = st.number_input("Condição Física (CTL)", min_value=0.0, step=0.1)

        # Botão de submissão
        submit_button = st.form_submit_button(label="Salvar Dados")

        if submit_button:
            # Função para substituir valores 0 por None
            def substitui_zero_por_none(valor):
                return None if valor == 0 else valor

            # Salvar medidas corporais
            nova_medida = {
                "Data": data.strftime("%Y-%m-%d"),
                "Peso (kg)": substitui_zero_por_none(peso),
                "Tórax (cm)": substitui_zero_por_none(torax),
                "Cintura (cm)": substitui_zero_por_none(cintura),
                "Abdômen (cm)": substitui_zero_por_none(abdomen),
                "Quadril (cm)": substitui_zero_por_none(quadril),
                "Braço Direito (cm)": substitui_zero_por_none(braco_direito),
                "Braço Esquerdo (cm)": substitui_zero_por_none(braco_esquerdo),
                "Coxa Direita (cm)": substitui_zero_por_none(coxa_direita),
                "Coxa Esquerda (cm)": substitui_zero_por_none(coxa_esquerda),
                "Panturrilha Direita (cm)": substitui_zero_por_none(panturrilha_direita),
                "Panturrilha Esquerda (cm)": substitui_zero_por_none(panturrilha_esquerda),
                "Observações": observacoes
            }
            medidas_collection.insert_one(nova_medida)

            # Salvar condições do treino
            nova_condicao = {
                "Data": data.strftime("%Y-%m-%d"),
                "TSB": substitui_zero_por_none(tsb),
                "Fadiga (ATL)": substitui_zero_por_none(fadiga),
                "Condição Física (CTL)": substitui_zero_por_none(condicao_fisica)
            }
            condicoes_treino_collection.insert_one(nova_condicao)

            st.success("Dados salvos com sucesso!")

# Aba 4: Análise e Progresso
with abas[3]:
    st.header("📊 Análise e Progresso")

    # Carregar treinos
    df_treinos = carregar_treinos()

    if not df_treinos.empty:
        # Converte a coluna de data para datetime
        df_treinos["Data"] = pd.to_datetime(df_treinos["Data"], format="%d/%m/%Y")

        # Seção de Filtros
        st.subheader("📅 Filtros de Período")
        col1, col2 = st.columns(2)

        # Filtro por intervalo de datas
        with col1:
            st.write("Selecionar período:")
            data_inicio, data_fim = st.date_input(
                "Selecione o intervalo",
                value=(df_treinos["Data"].min(), df_treinos["Data"].max()),
                min_value=df_treinos["Data"].min(),
                max_value=df_treinos["Data"].max(),
            )

        # Filtro por mês
        with col2:
            st.write("Filtrar por mês:")
            mes_selecionado = st.selectbox(
                "Selecione o mês:",
                options=["Todos os meses"] + list(df_treinos["Data"].dt.strftime("%B").unique()),
            )

        # Aplica os filtros
        df_filtrado = df_treinos.copy()
        if data_inicio and data_fim:
            df_filtrado = df_filtrado[(df_filtrado["Data"] >= pd.Timestamp(data_inicio)) & (df_filtrado["Data"] <= pd.Timestamp(data_fim))]

        if mes_selecionado and mes_selecionado != "Todos os meses":
            mes_index = pd.Timestamp(datetime.strptime(mes_selecionado, "%B")).month
            df_filtrado = df_filtrado[df_filtrado["Data"].dt.month == mes_index]

        # Reorganizar as colunas antes de exibir
        colunas_ordenadas = [
            "Data",  # Primeira coluna
            "Tipo de Treino",
            "Tempo Total (min)",
            "Calorias Queimadas",
            "Batimento Médio (bpm)",
            "Batimento Máximo (bpm)",
            "Zona Leve (min)",
            "Zona Intensa (min)",
            "Zona Aeróbica (min)",
            "Zona Anaeróbica (min)",
            "Zona Max. VO2 (min)",
            "Mobilidade (min)",
            "Aeróbico (min)",
            "Comentários"
        ]
        colunas_ordenadas = [col for col in colunas_ordenadas if col in df_filtrado.columns]
        df_reordenado = df_filtrado[colunas_ordenadas]

        # Exibir DataFrame filtrado e reordenado
        st.dataframe(df_reordenado)

        # Estatísticas gerais com base no filtro
        st.subheader("📈 Estatísticas Gerais")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total de Treinos", len(df_filtrado))

        with col2:
            st.metric("Tempo Total de Treino (min)", df_filtrado["Tempo Total (min)"].sum())
            st.metric("Tempo Médio de Treino (min)", df_filtrado["Tempo Total (min)"].mean().astype(int) if len(df_filtrado) > 0 else 0)

        with col3:
            st.metric("Total de Calorias Queimadas", df_filtrado["Calorias Queimadas"].sum())
            st.metric("Média de Calorias por Treino", df_filtrado["Calorias Queimadas"].mean().astype(int) if len(df_filtrado) > 0 else 0)

        # Gráficos de Progresso
        st.subheader("📊 Gráficos de Progresso")

        # Calorias acumuladas por dia
        calorias_acumuladas = df_treinos.groupby(df_treinos["Data"].dt.date)["Calorias Queimadas"].sum().reset_index()
        calorias_acumuladas.columns = ["Data", "Calorias Queimadas"]
        fig_calorias = px.bar(
            calorias_acumuladas, 
            x="Data", 
            y="Calorias Queimadas", 
            title="Calorias Queimadas",
            text="Calorias Queimadas"  # Adiciona o texto
        )
        fig_calorias.update_traces(
            textposition="outside",  # Posição do texto acima da barra
            texttemplate="%{text}"  # Exibe o valor no formato padrão
        )
        st.plotly_chart(fig_calorias, use_container_width=True)

        # Tempo de treino acumulado por dia
        tempo_acumulado = df_treinos.groupby(df_treinos["Data"].dt.date)["Tempo Total (min)"].sum().reset_index()
        tempo_acumulado.columns = ["Data", "Tempo Total (min)"]
        fig_tempo = px.bar(
            tempo_acumulado, 
            x="Data", 
            y="Tempo Total (min)", 
            title="Tempo Gasto",
            text="Tempo Total (min)"  # Adiciona o texto
        )
        fig_tempo.update_traces(
            textposition="outside",  # Posição do texto acima da barra
            texttemplate="%{text}"  # Exibe o valor no formato padrão
        )
        st.plotly_chart(fig_tempo, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para gerar análises ou gráficos.")

# Aba 5: Meta Anual e Indicador de Assiduidade
with abas[4]:
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

# Aba 6: Medidas Corporais
with abas[5]:  # Certifique-se de que esta seja a 5ª aba adicionada
    st.header("📏 Medidas Corporais")

    # Carregar dados de medidas corporais
    df_medidas = carregar_medidas()

    if not df_medidas.empty:
        # Conversão de tipos
        df_medidas["Data"] = pd.to_datetime(df_medidas["Data"], errors="coerce")
        
        # Garantir que todas as colunas de medidas estejam no formato float
        colunas_medidas = [
            "Peso (kg)", "Tórax (cm)", "Cintura (cm)", "Abdômen (cm)", 
            "Quadril (cm)", "Coxa Direita (cm)", "Coxa Esquerda (cm)", 
            "Panturrilha Direita (cm)", "Panturrilha Esquerda (cm)", 
            "Braço Direito (cm)", "Braço Esquerdo (cm)"
        ]
        for col in colunas_medidas:
            if col in df_medidas.columns:  # Verifica se a coluna existe
                df_medidas[col] = pd.to_numeric(df_medidas[col], errors="coerce")

        # Remover duplicatas e organizar por data
        df_medidas = df_medidas.drop_duplicates(subset=["Data"]).sort_values(by="Data")

        # Exibição da tabela
        st.dataframe(df_medidas)

        # Seleção de medidas para exibição no gráfico
        st.subheader("📊 Gráfico Temporal de Medidas")
        # Remove colunas irrelevantes se elas existirem
        colunas_irrelevantes = ["Data", "Observações", "_id"]
        colunas_validas = [col for col in df_medidas.columns if col not in colunas_irrelevantes]

        medidas_selecionadas = st.multiselect(
            "Selecione as Medidas para Exibir:",
            options=colunas_validas,
            default=colunas_validas[:2],  # Exibe as duas primeiras medidas por padrão
        )

        if medidas_selecionadas:
            # Criar gráfico temporal com base nas medidas selecionadas
            fig_medidas = px.line(
                df_medidas,
                x="Data",
                y=medidas_selecionadas,
                title="Evolução das Medidas ao Longo do Tempo",
                labels={"value": "Valor (cm ou kg)", "variable": "Medidas"},
            )
            fig_medidas.update_traces(
                mode="lines+markers+text",  # Adiciona valores como texto
                textposition="top center",  # Define a posição do texto
                texttemplate="%{y}"  # Exibe apenas os valores no texto
            )
            st.plotly_chart(fig_medidas, use_container_width=True)
        else:
            st.warning("Selecione ao menos uma medida para exibir no gráfico.")
    else:
        st.warning("Nenhuma medida corporal encontrada no banco de dados.")

# Aba 7: Indicadores de Treinos
with abas[6]:
    st.header("📊 Indicadores de Treinos e Progresso")

    # Cálculo da idade com base na data de nascimento
    data_nascimento = datetime(1990, 7, 27)  # Insira sua data de nascimento
    idade = (datetime.now() - data_nascimento).days // 365

    # Indicadores - Divisão do layout em 2 colunas
    col1, col2 = st.columns(2)

    # Coluna 1: Gráficos de distribuição e intensidade
    with col1:
        if not df_treinos.empty:
            st.subheader("📈 Treinos: Distribuição e Intensidade")
            
            # Distribuição de Tempo por Zona de Esforço
            zonas = ["Leve", "Intensa", "Aeróbica", "Anaeróbica", "VO2 Máximo"]
            tempos_zonas = [
                df_treinos["Zona Leve (min)"].sum(),
                df_treinos["Zona Intensa (min)"].sum(),
                df_treinos["Zona Aeróbica (min)"].sum(),
                df_treinos["Zona Anaeróbica (min)"].sum(),
                df_treinos["Zona Max. VO2 (min)"].sum(),
            ]
            fig_zonas = px.pie(
                names=zonas,
                values=tempos_zonas,
                title="Distribuição de Tempo por Zona de Esforço",
            )
            st.plotly_chart(fig_zonas, use_container_width=True)

        # Intensidade Média
        max_bpm = 220 - idade
        intensidade_media = (
            df_treinos["Batimento Médio (bpm)"].mean() / max_bpm * 100
            if max_bpm > 0
            else 0
        )
        st.metric("Intensidade Média (%)", f"{intensidade_media:.2f}%")

    # Coluna 2: Eficiência calórica e variedade de treinos
    with col2:
        st.subheader("📊 Eficiência e Variedade")
        
        # Eficiência Calórica
        total_calorias = df_treinos["Calorias Queimadas"].sum()
        total_tempo = df_treinos["Tempo Total (min)"].sum()
        eficiencia_calorica = total_calorias / total_tempo if total_tempo > 0 else 0
        st.metric("Calorias por Minuto", f"{eficiencia_calorica:.2f} cal/min")

        # Variedade de Treinos
        frequencias_treino = df_treinos["Tipo de Treino"].value_counts()
        fig_variedade = px.bar(
            x=frequencias_treino.index,
            y=frequencias_treino.values,
            labels={"x": "Tipo de Treino", "y": "Frequência"},
            title="Frequência por Tipo de Treino",
        )
        st.plotly_chart(fig_variedade, use_container_width=True)

    # Indicadores de Progresso Físico
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("📏 Progresso Físico")

        # Mudança em Medidas Corporais
        df_medidas["Data"] = pd.to_datetime(df_medidas["Data"])
        medidas_selecionadas = [
            "Tórax (cm)", "Cintura (cm)", "Abdômen (cm)", "Quadril (cm)"
        ]
        if not df_medidas.empty:
            fig_progresso_medidas = px.line(
                df_medidas,
                x="Data",
                y=medidas_selecionadas,
                title="Evolução das Medidas Corporais",
                labels={"value": "Medidas (cm)", "variable": "Medidas"},
            )
            fig_progresso_medidas.update_traces(
                mode="lines+markers+text",
                textposition="top center",
                texttemplate="%{y:.1f}",
                connectgaps=True,
            )
            st.plotly_chart(fig_progresso_medidas, use_container_width=True)

        # Mudança no Peso Corporal
        st.subheader("📉 Mudança no Peso Corporal")
        peso_meta = 58  # Meta de peso
        if "Peso (kg)" in df_medidas.columns:
            fig_peso = px.line(
                df_medidas,
                x="Data",
                y="Peso (kg)",
                title="Progresso do Peso Corporal",
                labels={"value": "Peso (kg)", "variable": "Peso"},
            )
            fig_peso.add_hline(
                y=peso_meta,
                line_dash="dot",
                annotation_text=f"Meta: {peso_meta} kg",
                annotation_position="bottom right",
                
            )
            fig_peso.update_traces(
                mode="lines+markers+text",
                textposition="top center",
                texttemplate="%{y:.1f}",
                connectgaps=True
            )
            st.plotly_chart(fig_peso, use_container_width=True)

    with col4:
        st.subheader("📈 Progressão de Carga")

        # Carregar registros de exercícios
        registros_exercicios = carregar_registros_exercicios()

        if registros_exercicios:  # Verifica se há registros disponíveis
            # Converter a lista de registros para um DataFrame
            df_registros_exercicios = pd.DataFrame(registros_exercicios)

            # Verifica se o DataFrame possui a coluna "Detalhes" e processa os dados
            if "Detalhes" in df_registros_exercicios.columns and not df_registros_exercicios.empty:
                registros_detalhes = []
                for _, registro in df_registros_exercicios.iterrows():
                    if "Detalhes" in registro and isinstance(registro["Detalhes"], list):
                        for detalhe in registro["Detalhes"]:
                            detalhe["Data"] = registro["Data do Registro"]  # Adiciona a data do registro
                            registros_detalhes.append(detalhe)

                # Transformar os detalhes em DataFrame
                df_detalhes = pd.DataFrame(registros_detalhes)

                if not df_detalhes.empty:
                    # Garantir que as colunas estão no formato correto
                    if "Peso (kg)" in df_detalhes.columns:
                        df_detalhes["Peso (kg)"] = pd.to_numeric(df_detalhes["Peso (kg)"], errors="coerce")

                    if "Data" in df_detalhes.columns:
                        df_detalhes["Data"] = pd.to_datetime(df_detalhes["Data"], format="%Y-%m-%d")
                        df_detalhes["Data"] = df_detalhes["Data"].dt.strftime("%d/%m/%Y")

                    # Selecionar exercícios para exibição no gráfico
                    exercicios_disponiveis = df_detalhes["Exercício"].unique().tolist()
                    exercicios_selecionados = st.multiselect(
                        "Selecione os Exercícios para Visualizar:",
                        options=exercicios_disponiveis,
                        default=exercicios_disponiveis[:5],  # Seleciona os 5 primeiros por padrão
                    )

                    # Filtrar os dados para os exercícios selecionados
                    df_filtrado = df_detalhes[df_detalhes["Exercício"].isin(exercicios_selecionados)]

                    if not df_filtrado.empty:
                        # Criar o gráfico de progressão de carga
                        fig_carga = px.line(
                            df_filtrado,
                            x="Data",
                            y="Peso (kg)",
                            color="Exercício",
                            title="Evolução de Carga nos Exercícios Selecionados",
                            labels={"Data": "Data", "Peso (kg)": "Carga (kg)", "Exercício": "Exercício"},
                            markers=True
                        )
                        fig_carga.update_traces(connectgaps=True)
                        st.plotly_chart(fig_carga, use_container_width=True)
                    else:
                        st.warning("Nenhum dado encontrado para os exercícios selecionados.")
                else:
                    st.warning("Nenhum detalhe de exercícios disponível.")
            else:
                st.warning("Nenhum dado válido encontrado nos registros de exercícios.")
        else:
            st.warning("Nenhum registro de exercícios encontrado.")

        # Volume Total do Treino
        st.subheader("📊 Volume Total por Grupo Muscular")

        # Carregar registros de exercícios e exercícios do banco de dados
        registros_exercicios = carregar_registros_exercicios()
        df_exercicios = carregar_exercicios()

        if registros_exercicios and not df_exercicios.empty:
            # Converter registros para DataFrame
            df_registros_exercicios = pd.DataFrame(registros_exercicios)

            # Verifica se "Detalhes" e "Data do Registro" estão presentes
            if "Detalhes" in df_registros_exercicios.columns and "Data do Registro" in df_registros_exercicios.columns:
                registros_detalhes = []
                for _, registro in df_registros_exercicios.iterrows():
                    if isinstance(registro["Detalhes"], list):
                        for detalhe in registro["Detalhes"]:
                            detalhe["Data"] = registro["Data do Registro"]  # Adiciona a data do registro
                            registros_detalhes.append(detalhe)

                # Transformar os detalhes em DataFrame
                df_detalhes = pd.DataFrame(registros_detalhes)

                if not df_detalhes.empty:
                    # Garantir os tipos corretos das colunas
                    df_detalhes["Peso (kg)"] = pd.to_numeric(df_detalhes["Peso (kg)"], errors="coerce")
                    df_detalhes["Repetições"] = pd.to_numeric(df_detalhes["Repetições"], errors="coerce")
                    df_detalhes["Data"] = pd.to_datetime(df_detalhes["Data"], format="%Y-%m-%d")

                    # Combinar os registros com o número de séries do banco de exercícios
                    df_combinado = pd.merge(
                        df_detalhes,
                        df_exercicios[["nome", "series", "musculo"]],
                        left_on="Exercício",
                        right_on="nome",
                        how="inner"
                    )

                    # Calcular o volume total: Peso (kg) * Repetições * Séries
                    df_combinado["volume_total"] = df_combinado["Peso (kg)"] * df_combinado["Repetições"] * df_combinado["series"]

                    # Agrupar por grupo muscular e somar o volume total
                    volume_por_musculo = df_combinado.groupby("musculo")["volume_total"].sum().reset_index()

                    # Criar gráfico de barras
                    fig_volume = px.bar(
                        volume_por_musculo,
                        x="musculo",
                        y="volume_total",
                        title="Volume Total por Grupo Muscular",
                        text="volume_total",
                        labels={"musculo": "Grupo Muscular", "volume_total": "Volume Total (kg)"},
                    )
                    fig_volume.update_traces(textposition="outside")
                    st.plotly_chart(fig_volume, use_container_width=True)
                else:
                    st.warning("Nenhum detalhe de exercícios disponível.")
            else:
                st.warning("Os registros de exercícios não possuem os campos esperados.")
        else:
            st.warning("Nenhum dado disponível para calcular o volume total.")

    # Indicadores de Recuperação
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("💤 Indicadores de Recuperação")

        df_condicoes = carregar_condicoes()
        if not df_condicoes.empty:
            numeric_columns = ["TSB", "Fadiga (ATL)", "Condição Física (CTL)"]
            for col in numeric_columns:
                df_condicoes[col] = pd.to_numeric(df_condicoes[col], errors="coerce")

            df_long = df_condicoes.melt(
                id_vars="Data", 
                value_vars=numeric_columns, 
                var_name="Indicador", 
                value_name="Valor"
            )
            df_long["Data"] = pd.to_datetime(df_long["Data"], errors="coerce")
            df_long = df_long.dropna(subset=["Valor", "Data"])

            fig_fadiga = px.line(
                df_long,
                x="Data",
                y="Valor",
                color="Indicador",
                title="Evolução dos Indicadores de Recuperação",
                markers=True
            )
            fig_fadiga.update_traces(
                mode="lines+markers+text",
                textposition="top center",
                texttemplate="%{y:.1f}",
                connectgaps=True
            )
            st.plotly_chart(fig_fadiga, use_container_width=True)

    with col6:
        # Relação Treino/Recuperação
        df_treinos = carregar_treinos()

        if not df_treinos.empty:
            # Converte a coluna de data para datetime
            df_treinos["Data"] = pd.to_datetime(df_treinos["Data"], format="%d/%m/%Y")

            # Cálculo do número de dias corridos no ano até hoje
            hoje = datetime.now()
            inicio_ano = datetime(hoje.year, 1, 1)
            dias_corridos = (hoje - inicio_ano).days + 1  # Inclui o dia atual

            # Dias treinados com mais de 300 calorias queimadas
            dias_treinados = df_treinos[df_treinos["Calorias Queimadas"] > 300]["Data"].nunique()

            # Relação Treino/Recuperação
            relacao_treino_recuperacao = dias_treinados / dias_corridos if dias_corridos > 0 else 0

            # Criar DataFrame para o gráfico
            df_recuperacao = pd.DataFrame({
                "Indicador": ["Dias Corridos", "Dias Treinados"],
                "Valor": [dias_corridos, dias_treinados]
            })

            # Criar figura com eixo duplo
            fig_recuperacao = px.bar(
                df_recuperacao,
                x="Indicador",
                y="Valor",
                title="Relação Treino/Recuperação",
                text="Valor",
                labels={"Indicador": "Indicador", "Valor": "Valor"},
            )

            # Adicionar o eixo secundário para a relação treino/recuperação
            fig_recuperacao.add_scatter(
                x=["Relação Treino/Recuperação"],
                y=[relacao_treino_recuperacao * 100],  # Converter para percentual
                mode="markers+text",
                text=[f"{relacao_treino_recuperacao:.0%}"],  # Exibir como percentual
                textposition="top center",
                name="Relação (%)",
                yaxis="y2"
            )

            # Atualizar layout para incluir o eixo direito
            fig_recuperacao.update_layout(
                yaxis2=dict(
                    title="Relação Treino/Recuperação (%)",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                ),
                yaxis=dict(title="Dias"),
            )

            st.plotly_chart(fig_recuperacao, use_container_width=True)

        else:
            st.warning("Nenhum dado de treino encontrado no banco de dados.")


# Executar a aplicação
