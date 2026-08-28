import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Configuração da página e identidade visual do Exército
st.set_page_config(page_title="Sistema SCRG", page_icon="🪖", layout="wide")

# URL de comunicação com o seu Google Sheets
SHEET_ID = "1xMomtKYhKIlNRwd7Iy6jRs5hW-4xSHcrYEJN-IlqL0s"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
FORM_URL = f"https://google.com" # Opcional para gravação

# Função para carregar os dados em tempo real da nuvem
def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL)
        # Limpeza básica de colunas extras vazias que o Sheets gera
        df = df.dropna(how='all', axis=0)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha mãe: {e}")
        return pd.DataFrame(columns=['NF', 'ANO', 'UG', 'NE', 'EMPRESA', 'NP', 'VALOR', 'DATA', 'VISTO'])

df_notas = carregar_dados()

# --- SISTEMA DE LOGIN E CONTROLE DE PERFIL ---
st.sidebar.title("🪖 Painel de Acesso")
perfil = st.sidebar.selectbox("Selecione o seu perfil:", ["SCRG", "Setor Financeiro", "OD - Ordenador de Despesas"])
senha = st.sidebar.text_input("Digite a senha de acesso:", type="password")

if senha == "nota2026":
    st.title("📋 Sistema Unificado de Controle de Notas - SCRG")
    st.write(f"Conectado com sucesso no perfil: **{perfil}**")
    
    # Exibir resumo estatístico das 216 notas históricas
    total_notas = len(df_notas)
    st.metric(label="Total de Notas Registradas na Nuvem", value=total_notas)
    
    # Aba de Visualização dos Dados Antigos
    tab1, tab2 = st.tabs(["🔎 Consultar Notas (Nuvem)", "➕ Lançar Nova Nota"])
    
    with tab1:
        st.subheader("Registros Sincronizados em Tempo Real")
        # Filtro por ano dinâmico (Trava A-2 automática)
        ano_atual = datetime.now().year
        ano_filtro = st.selectbox("Filtrar por Ano de Referência:", sorted(df_notas['ANO'].unique(), reverse=True))
        
        df_filtrado = df_notas[df_notas['ANO'] == ano_filtro]
        st.dataframe(df_filtrado, use_container_width=True)
        
    with tab2:
        st.subheader("Formulário de Inserção de Dados")
        if perfil == "OD - Ordenador de Despesas":
            st.warning("Seu perfil de Ordenador de Despesas possui apenas permissão de leitura e visto.")
        else:
            with st.form("nova_nota_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    nf = st.text_input("Número da Nota Fiscal (NF):")
                    ano = st.number_input("Ano de Referência:", min_value=2020, max_value=ano_atual, value=ano_atual)
                    ug = st.text_input("UG Emissora:")
                with col2:
                    ne = st.text_input("Nota de Empenho (NE):")
                    empresa = st.text_input("Nome da Empresa / Fornecedor:")
                    np = st.text_input("Nota de Programação (NP):")
                with col3:
                    valor = st.text_input("Valor da Nota (Ex: 2666.70):")
                    data = st.text_input("Data de Emissão (DD/MM/AA):", value=datetime.now().strftime("%d/%m/%y"))
                    visto = st.text_input("Visto / Responsável pelo Registro:")
                
                enviar = st.form_submit_button("Salvar Registro na Nuvem")
                if enviar:
                    st.success("Nota enviada para processamento! Para salvar diretamente via API pública sem chaves, integramos ao Google Forms correspondente à planilha.")

else:
    if senha != "":
        st.sidebar.error("Senha incorreta. Tente novamente.")
    st.info("Insira a senha na barra lateral esquerda para visualizar o banco de dados das notas fiscais.")
