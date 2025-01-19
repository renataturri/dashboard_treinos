import streamlit as st
import pandas as pd

# Configurar página para celular com título e ícone
st.set_page_config(
    page_title="Placar Carioca",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        h1 {
            font-size: 12px; /* Título principal */
        }
        h2 {
            font-size: 10px; /* Subtítulos */
        }
        h3 {
            font-size: 8px; /* Subsubtítulos */
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Título do app
st.title("Carioquinha")

# Inicializar estado da sessão
if "jogadores" not in st.session_state:
    st.session_state.jogadores = []
if "pontuacoes" not in st.session_state:
    st.session_state.pontuacoes = pd.DataFrame()
if "rodada_atual" not in st.session_state:
    st.session_state.rodada_atual = 1
if "jogo_terminado" not in st.session_state:
    st.session_state.jogo_terminado = False
if "jogo_iniciado" not in st.session_state:
    st.session_state.jogo_iniciado = False  # Variável de controle para início do jogo

# Controle para Registro de Jogadores
if not st.session_state.jogo_iniciado:
    st.header("Jogadores")

    # Entrada para o número de jogadores
    num_jogadores = st.number_input(
        "Número de jogadores:",
        min_value=2,
        max_value=10,
        step=1,
        value=2,
        key="num_jogadores",
    )

    # Formulário para registrar os jogadores
    with st.form("registro_jogadores"):
        nomes = [
            st.text_input(f"Nome do jogador {i + 1}:", key=f"jogador_nome_{i}")
            for i in range(num_jogadores)
        ]
        iniciar = st.form_submit_button("Salvar Jogadores")

        # Lógica para salvar os nomes dos jogadores e iniciar o jogo
        if iniciar:
            if all(nomes):  # Verifica se todos os nomes foram preenchidos
                st.session_state.jogadores = nomes
                st.session_state.pontuacoes = pd.DataFrame(
                    {nome: [] for nome in nomes}, index=pd.Index([], name="Rodada")
                )
                st.session_state.jogo_iniciado = True  # Marca o jogo como iniciado
                st.success("Jogadores registrados com sucesso! Iniciando o jogo...")
                jogar = st.form_submit_button("Iniciar Jogo")
                st.stop()  # Interrompe a execução para redesenhar a interface
            else:
                st.error("Por favor, preencha todos os nomes.")

# Registro de Pontuações por Rodada (aparece após o jogo ser iniciado)
if st.session_state.jogo_iniciado and not st.session_state.jogo_terminado:
    st.header("Registro de Pontuações")

    # Determinar o número de cartas para a rodada atual
    cartas_por_rodada = min(6 + st.session_state.rodada_atual - 1, 13)

    # Exibir informações da rodada
    st.subheader(f"Rodada {st.session_state.rodada_atual}: {cartas_por_rodada} cartas")

    # Formulário para entrada de pontuações
    with st.form("registro_pontuacoes"):
        st.write("Insira as pontuações dos jogadores:")
        pontos = {
            nome: st.number_input(
                f"Pontos de {nome}:", min_value=0, step=1, key=f"pontos_{nome}_rodada_{st.session_state.rodada_atual}"
            )
            for nome in st.session_state.jogadores
        }
        salvar = st.form_submit_button("Salvar Pontuação")

        # Lógica para salvar as pontuações e avançar para a próxima rodada
        if salvar:
            # Salva os pontos da rodada atual
            st.session_state.pontuacoes = pd.concat(
                [
                    st.session_state.pontuacoes,
                    pd.DataFrame([pontos], index=[st.session_state.rodada_atual]),
                ]
            )
            st.success(f"Pontuações da Rodada {st.session_state.rodada_atual} registradas!")
            # Avança para a próxima rodada, se ainda houver rodadas
            proxima_rodada = st.form_submit_button("Próxima Rodada")
            if st.session_state.rodada_atual < 8:
                st.session_state.rodada_atual += 1
            else:
                st.session_state.jogo_terminado = True


# Exibição dos Resultados
if st.session_state.pontuacoes is not None and not st.session_state.pontuacoes.empty:
    st.header("💰 Resultados Acumulados 💰")

    # Exibir a tabela de pontuações por rodada
    st.subheader("📊 Tabela de Pontuações por Rodada")
    st.dataframe(st.session_state.pontuacoes)

    # Calcular as pontuações acumuladas
    pontuacoes_acumuladas = st.session_state.pontuacoes.cumsum()

    # Adicionar uma linha "TOTAL" com a soma final
    total = pd.DataFrame(pontuacoes_acumuladas.iloc[-1]).T
    total.index = ["TOTAL"]

    # Exibir a tabela de pontuações acumuladas
    ##st.subheader("Tabela de Pontuações Acumuladas")
    ##tabela_final = pd.concat([pontuacoes_acumuladas, total])
    ##st.dataframe(tabela_final)

    # Exibir o ranking atual
    st.subheader("🏆 Ranking Atual")
    ranking = pontuacoes_acumuladas.iloc[-1].sort_values()
    for i, (jogador, pontos) in enumerate(ranking.items(), start=1):
        st.write(f"**{i}º Lugar:** {jogador} com {pontos} pontos.")

    # Mensagem final ao término do jogo
    if st.session_state.jogo_terminado:
        campeao = ranking.idxmin()
        menor_pontuacao = ranking.min()
        st.success(f"🎉 Parabéns, {campeao}! Você venceu com apenas {menor_pontuacao} pontos! 🎉")

        # Botão para iniciar uma nova partida
        if st.button("Iniciar Nova Partida"):
            st.session_state.clear()