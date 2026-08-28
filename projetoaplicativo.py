import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Configuração da página e identidade visual do Exército
st.set_page_config(page_title="Sistema SCRG", page_icon="🪖", layout="wide")

# URLs de comunicação com a planilha e o formulário do Google
SHEET_ID = "1xMomtKYhKIlNRwd7Iy6jRs5hW-4xSHcrYEJN-IlqL0s"
CSV_URL = f"https://google.com{SHEET_ID}/gviz/tq?tqx=out:csv"
FORM_URL = "https://google.com"

def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL)
        df = df.dropna(how='all', axis=0)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        # Trata o ano para garantir que seja exibido como texto/inteiro sem .0
        if 'ANO' in df.columns:
            df['ANO'] = df['ANO'].fillna(0).astype(int).astype(str)
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
    
    total_notas = len(df_notas)
    st.metric(label="Total de Notas Registradas na Nuvem", value=total_notas)
    
    tab1, tab2 = st.tabs(["🔎 Consultar Notas (Nuvem)", "➕ Lançar Nova Nota"])
    
    with tab1:
        st.subheader("Registros Sincronizados em Tempo Real")
        anos_disponiveis = sorted(df_notas['ANO'].unique(), reverse=True)
        if "0" in anos_disponiveis: anos_disponiveis.remove("0")
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
                    np = st.text_input("Nota de Programação (NP):")
                with col3:
                    valor = st.text_input("Valor da Nota (Ex: 2666.70):")
                    data = st.text_input("Data de Emissão (DD/MM/AA):", value=datetime.now().strftime("%d/%m/%y"))
                    visto = st.text_input("Visto / Responsável pelo Registro:")
                
                enviar = st.form_submit_button("Salvar Registro na Nuvem")
                
                if enviar:
                    if not nf or not empresa:
                        st.error("Por favor, preencha os campos obrigatórios (NF e Empresa).")
                    else:
                        # Mapeamento exato das caixas do Google Forms (ordem de criação)
                        dados_envio = {
                            "entry.921319728": nf,       # Campo NF
                            "entry.1741530931": ano,     # Campo ANO
                            "entry.2069730598": ug,      # Campo UG
                            "entry.604113110": ne,       # Campo NE
                            "entry.533276632": empresa,  # Campo EMPRESA
                            "entry.1011559868": np,      # Campo NP
                            "entry.25471464": valor,     # Campo VALOR
                            "entry.1691238965": data,    # Campo DATA
                            "entry.2057630768": visto     # Campo VISTO
                        }
                        try:
                            resposta = requests.post(FORM_URL, data=dados_envio)
                            if resposta.status_code == 200:
                                st.success("Nota salva com sucesso na nuvem! Atualize a página de consulta para ver o novo registro.")
                                st.balloons()
                            else:
                                st.error("Erro temporário ao enviar para o banco de dados. Tente novamente.")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

else:
    if senha != "":
        st.sidebar.error("Senha incorreta. Tente novamente.")
    st.info("Insira a senha na barra lateral esquerda para visualizar o banco de dados das notas fiscais.")# atualizado
