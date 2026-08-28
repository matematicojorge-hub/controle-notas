import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime

# Configuração da página e identidade visual do Exército
st.set_page_config(page_title="Sistema SCRG", page_icon="🪖", layout="wide")

# Link de comunicação direto e travado na aba certa (Totalmente Corrigido)
SHEET_ID = "1xMomtKYhKIlNRwd7Iy6jRs5hW-4xSHcrYEJN-IlqL0s"
CSV_URL = f"https://google.com{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=dados"
FORM_URL = "https://google.com"

def carregar_dados():
    try:
        resposta = requests.get(CSV_URL, timeout=10)
        resposta.raise_for_status()
        df = pd.read_csv(io.StringIO(resposta.text))

        df = df.dropna(how='all', axis=0)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        if 'ANO' in df.columns:
            df['ANO'] = df['ANO'].fillna(0).astype(int).astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha mãe: {e}")
        return pd.DataFrame(columns=['NF', 'ANO', 'UG', 'NE', 'EMPRESA', 'NP', 'VALOR', 'DATA', 'VISTO'])

df_notas = carregar_dados()

# --- SISTEMA DE LOGIN DIRETO (SEM SECRETS) ---
st.sidebar.title("🪖 Painel de Acesso")
perfil = st.sidebar.selectbox(
    "Selecione o seu perfil:",
    ["SCRG", "Setor Financeiro", "OD - Ordenador de Despesas"]
)
senha = st.sidebar.text_input("Digite a senha de acesso:", type="password")

# Definição simples e direta das senhas por setor
SENHAS_DIRETAS = {
    "SCRG": "nota2026",
    "Setor Financeiro": "fin2026",
    "OD - Ordenador de Despesas": "od2026"
}

acesso_liberado = senha != "" and senha == SENHAS_DIRETAS.get(perfil)

if acesso_liberado:
    st.title("📋 Sistema Unificado de Controle de Notas - SCRG")
    st.write(f"Conectado com sucesso no perfil: **{perfil}**")

    total_notas = len(df_notas)
    st.metric(label="Total de Notas Registradas na Nuvem", value=total_notas)

    tab1, tab2 = st.tabs(["🔎 Consultar Notas (Nuvem)", "➕ Lançar Nova Nota"])

    with tab1:
        st.subheader("Registros Sincronizados em Tempo Real")
        if df_notas.empty or 'ANO' not in df_notas.columns:
            st.warning("Nenhum registro disponível no momento.")
        else:
            anos_disponiveis = sorted(df_notas['ANO'].unique(), reverse=True)
            if "0" in anos_disponiveis:
                anos_disponiveis.remove("0")

            if not anos_disponiveis:
                st.warning("Nenhum ano de referência encontrado nos registros.")
            else:
                ano_filtro = st.selectbox("Filtrar por Ano de Referência:", anos_disponiveis)
                df_filtrado = df_notas[df_notas['ANO'] == ano_filtro]
                st.dataframe(df_filtrado, use_container_width=True)

    with tab2:
        st.subheader("Formulário de Inserção de Dados")
        if perfil == "OD - Ordenador de Despesas":
            st.warning("Seu perfil de Ordenador de Despesas possui apenas permissão de leitura e visto.")
        else:
            with st.form("nova_nota_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    nf = st.text_input("Número da Nota Fiscal (NF):")
                    ano = st.text_input("Ano de Referência:", value=str(datetime.now().year))
                    ug = st.text_input("UG Emissora:")
                with col2:
                    ne = st.text_input("Nota de Empenho (NE):")
                    empresa = st.text_input("Nome da Empresa / Fornecedor:")
                    np_campo = st.text_input("Nota de Programação (NP):")
                with col3:
                    valor = st.text_input("Valor da Nota (Ex: 2666.70):")
                    data = st.text_input("Data de Emissão (DD/MM/AA):", value=datetime.now().strftime("%d/%m/%y"))
                    visto = st.text_input("Visto / Responsável pelo Registro:")

                enviar = st.form_submit_button("Salvar Registro na Nuvem")

                if enviar:
                    if not nf or not empresa:
                        st.error("Por favor, preencha os campos obrigatórios (NF e Empresa).")
                    else:
                        dados_envio = {
                            "entry.921319728": nf,
                            "entry.1741530931": ano,
                            "entry.2069730598": ug,
                            "entry.604113110": ne,
                            "entry.533276632": empresa,
                            "entry.1011559868": np_campo,
                            "entry.25471464": valor,
                            "entry.1691238965": data,
                            "entry.2057630768": visto,
                        }
                        try:
                            resposta = requests.post(FORM_URL, data=dados_envio, timeout=10)
                            if resposta.status_code == 200:
                                st.success("Nota salva com sucesso na nuvem! Atualize a página de consulta para ver o novo registro.")
                                st.balloons()
                            else:
                                st.error(f"Erro ao enviar para o banco de dados (status {resposta.status_code}). Tente novamente.")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

else:
    if senha != "":
        st.sidebar.error("Senha incorreta. Tente novamente.")
    st.info("Insira a senha na barra lateral esquerda para visualizar o banco de dados das notas fiscais.")
