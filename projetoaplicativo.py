import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Configuração da página responsiva
st.set_page_config(page_title="Gerenciador de Notas", layout="wide")

DB_NAME = "banco_dados.db"
BACKUP_NAME = "backup_notas.csv"

# Inicializa o banco de dados
def inicializar_sistema():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            NF TEXT, ANO TEXT, UG TEXT, NE TEXT, 
            EMPRESA TEXT, NP TEXT, OB TEXT, VALOR REAL, 
            DATA TEXT, VISTO TEXT, STATUS TEXT
        )
    ''')
    cursor.execute('CREATE TABLE IF NOT EXISTS responsaveis (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE)')
    
    cursor.execute("SELECT COUNT(*) FROM responsaveis")
    if cursor.fetchone() == 0:
        nomes_iniciais = ["TEN MIQUEIAS", "SGT CAMPOS", "CB MIGUEL"]
        cursor.executemany("INSERT INTO responsaveis (nome) VALUES (?)", [(n,) for n in nomes_iniciais])
        
    conn.commit()
    conn.close()

def formatar_real(valor):
    try: return f"R$ {float(valor):,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    except: return "R$ 0,00"

def formatar_data_br(data_str):
    if not data_str or data_str in ["None", "NaT", ""]: return ""
    try: 
        data_limpa = data_str.split()[0]
        return datetime.strptime(data_limpa, '%Y-%m-%d').strftime('%d/%m/%Y')
    except: return data_str

def gerar_backup_csv():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM documentos", conn)
    conn.close()
    df.to_csv(BACKUP_NAME, index=False, encoding='utf-8-sig')

# CONTROLE DE ACESSO INDIVIDUAL INCLUINDO O CHEFE (OD)
def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if "perfil_usuario" not in st.session_state:
        st.session_state["perfil_usuario"] = ""
    if "senha_sistema" not in st.session_state:
        st.session_state["senha_sistema"] = "nota2026"

    if not st.session_state["autenticado"]:
        st.subheader("🔐 Acesso Restrito ao Sistema")
        # Inclusão estratégica do Ordenador de Despesas (OD)
        setor = st.selectbox("Selecione o seu Setor/Perfil:", [
            "SCRG - Conformidade de Gestão", 
            "Setor Financeiro",
            "OD - Ordenador de Despesas (Chefe)"
        ])
        senha = st.text_input("Digite a Senha de Acesso:", type="password")
        
        if st.button("Entrar no Sistema"):
            if senha == st.session_state["senha_sistema"]:
                st.session_state["autenticado"] = True
                if "SCRG" in setor:
                    st.session_state["perfil_usuario"] = "SCRG"
                elif "Financeiro" in setor:
                    st.session_state["perfil_usuario"] = "FINANCEIRO"
                else:
                    st.session_state["perfil_usuario"] = "OD"
                st.success("Acesso liberado!")
                st.rerun()
            else:
                st.error("Senha incorreta!")
        return False
    return True

inicializar_sistema()

st.title("📊 Sistema Avançado de Controle de Notas")

# Trava de Segurança por Perfil
if verificar_senha():
    is_scrg = st.session_state["perfil_usuario"] == "SCRG"
    is_od = st.session_state["perfil_usuario"] == "OD"
    
    # Carrega dados para autocomplete
    conn = sqlite3.connect(DB_NAME)
    empresas_cadastradas = sorted(list(set([str(r).strip().upper() for r in conn.execute("SELECT DISTINCT EMPRESA FROM documentos").fetchall() if r])))
    militares_cadastrados = sorted([str(r) for r in conn.execute("SELECT nome FROM responsaveis").fetchall()])
    conn.close()

    # Abas de navegação
    aba_cadastro, aba_financeiro, aba_departamento, aba_backup, aba_config = st.tabs([
        "📥 Inserir Documento", "✅ Visto do Financeiro", "⚙️ Controle (NP / OB)", "💾 Reservas e Auditoria", "⚙️ Configurações"
    ])

    # 1. ABA DE CADASTRO
    with aba_cadastro:
        st.header("Lançamento Inicial da Nota")
        if not is_scrg:
            st.warning("⚠️ Apenas usuários do setor SCRG podem inserir novos documentos.")
        
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nf = st.text_input("Nota Fiscal (NF)", disabled=not is_scrg)
                ano_atual = datetime.now().year
                anos_p = [str(ano_atual - 2), str(ano_atual - 1), str(ano_atual)]
                ano_selecionado = st.selectbox("Ano de Exercício (Regra A-2)", anos_p, index=2, disabled=not is_scrg)
                ug_selecionada = st.radio("Unidade Gestora (UG)", ["160146", "167146"], horizontal=True, disabled=not is_scrg)
                ne = st.text_input("Nota de Empenho (NE)", disabled=not is_scrg)
            with col2:
                opcoes_empresa = ["-- Digitar Nova Empresa --"] + empresas_cadastradas
                empresa_escolha = st.selectbox("Selecione uma Empresa", opcoes_empresa, disabled=not is_scrg)
                empresa_final = st.text_input("Nome da Nova Empresa", disabled=not is_scrg).upper() if empresa_escolha == "-- Digitar Nova Empresa --" else empresa_escolha
                valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f", disabled=not is_scrg)
            
            if st.form_submit_button("Gravar Documento", disabled=not is_scrg):
                if nf and empresa_final:
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("INSERT INTO documentos (NF, ANO, UG, NE, EMPRESA, NP, OB, VALOR, DATA, VISTO, STATUS) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                 (nf, ano_selecionado, ug_selecionada, ne, empresa_final, "", "", valor, "", "", "Pendente"))
                    conn.commit()
                    conn.close()
                    gerar_backup_csv()
                    st.success("Documento gravado!")
                    st.rerun()    # 2. ABA DO FINANCEIRO
    with aba_financeiro:
        st.header("Visto do Financeiro")
        if is_od:
            st.info("👀 Modo de Auditoria: O Ordenador de Despesas possui acesso de leitura às informações.")
            
        conn = sqlite3.connect(DB_NAME)
        df_pendentes = pd.read_sql_query("SELECT * FROM documentos WHERE STATUS = 'Pendente'", conn)
        conn.close()
        if df_pendentes.empty:
            st.info("Nenhum documento pendente.")
        else:
            opcoes = {f"NF: {r['NF']} | {r['EMPRESA']}": r['id'] for _, r in df_pendentes.iterrows()}
            id_doc = opcoes[st.selectbox("Selecione o documento físico entregue:", list(opcoes.keys()))]
            with st.form("form_validacao"):
                visto_nome = st.selectbox("Responsável pelo Recebimento", militares_cadastrados, disabled=is_od)
                data_hoje = st.date_input("Data de Recebimento", value=datetime.today(), disabled=is_od)
                if st.form_submit_button("Confirmar Recebimento", disabled=is_od):
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("UPDATE documentos SET DATA=?, VISTO=?, STATUS='Liquidado' WHERE id=?", (str(data_hoje), visto_nome, id_doc))
                    conn.commit()
                    conn.close()
                    gerar_backup_csv()
                    st.success("Recebimento confirmado!")
                    st.rerun()

    # 3. ABA DE CONTROLE (NP / OB) - EXCLUSIVA SCRG
    with aba_departamento:
        st.header("Gerenciamento do Fluxo e Alterações")
        if not is_scrg:
            st.error("🔒🔒🔒 Acesso Negado. Apenas o setor SCRG possui permissão para alterar ou excluir registros.")
        else:
            conn = sqlite3.connect(DB_NAME)
            df_todos = pd.read_sql_query("SELECT * FROM documentos", conn)
            conn.close()
            if df_todos.empty:
                st.info("Nenhum documento cadastrado.")
            else:
                opcoes_edicao = {f"ID {r['id']} - NF: {r['NF']} | {r['EMPRESA']}": r['id'] for _, r in df_todos.iterrows()}
                id_editar = opcoes_edicao[st.selectbox("Selecione o documento para controle:", list(opcoes_edicao.keys()))]
                dados_atuais = df_todos[df_todos['id'] == id_editar].iloc[0]
                
                # Exibe a data do visto formatada corretamente em DD/MM/AAAA
                data_visto_formatada = formatar_data_br(str(dados_atuais['DATA']))
                if data_visto_formatada:
                    st.info(f"📅 Data atual do Visto deste documento: {data_visto_formatada}")
                
                with st.form("form_edicao"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        edit_nf = st.text_input("Nota Fiscal (NF)", value=str(dados_atuais['NF']))
                        ano_at = datetime.now().year
                        anos_p_ed = [str(ano_at - 2), str(ano_at - 1), str(ano_at)]
                        
                        # Correção definitiva do final .0 no ano
                        ano_doc = str(dados_atuais['ANO']).split('.')[0] if dados_atuais['ANO'] else str(ano_at)
                        if ano_doc not in anos_p_ed: anos_p_ed.insert(0, ano_doc)
                        edit_ano = st.selectbox("Ano", anos_p_ed, index=anos_p_ed.index(ano_doc))
                        
                        edit_ug = st.selectbox("UG", ["160146", "167146"], index=0 if "160" in str(dados_atuais['UG']) else 1)
                        edit_ne = st.text_input("NE", value=str(dados_atuais['NE']))
                    with c2:
                        edit_empresa = st.text_input("Empresa", value=str(dados_atuais['EMPRESA'])).upper()
                        lista_status = ["Pendente", "Liquidado", "Pago"]
                        st_atual = dados_atuais['STATUS'] if dados_atuais['STATUS'] in lista_status else "Liquidado"
                        edit_status = st.selectbox("Status", lista_status, index=lista_status.index(st_atual))
                        bloquear_np = edit_status == "Pendente"
                        edit_np = st.text_input("NP", value=str(dados_atuais['NP'] if dados_atuais['NP'] else ""), disabled=bloquear_np)
                        bloquear_ob = edit_status != "Pago"
                        edit_ob = st.text_input("OB", value=str(dados_atuais['OB'] if dados_atuais['OB'] else ""), disabled=bloquear_ob)
                    with c3:
                        edit_valor = st.number_input("Valor", value=float(dados_atuais['VALOR'] if dados_atuais['VALOR'] else 0.0), min_value=0.0, step=0.01, format="%.2f")
                        edit_visto = st.selectbox("Visto", ["EM BRANCO"] + militares_cadastrados, index=0 if not dados_atuais['VISTO'] or dados_atuais['VISTO'] not in militares_cadastrados else militares_cadastrados.index(dados_atuais['VISTO']) + 1)
                        dt_str = dados_atuais['DATA']
                        dt_visto = datetime.today()
                        if dt_str and dt_str != "None" and dt_str != "":
                            try: dt_visto = datetime.strptime(dt_str.split()[0], '%Y-%m-%d')
                            except: pass
                        edit_data = st.date_input("Nova Data do Visto", value=dt_visto)
                    
                    if st.form_submit_button("💾 Atualizar Documento"):
                        v_final = "" if edit_visto == "EM BRANCO" else edit_visto
                        conn = sqlite3.connect(DB_NAME)
                        conn.execute("UPDATE documentos SET NF=?, ANO=?, UG=?, NE=?, EMPRESA=?, NP=?, OB=?, VALOR=?, DATA=?, VISTO=?, STATUS=? WHERE id=?",
                                     (edit_nf, edit_ano, edit_ug, edit_ne, edit_empresa, "" if bloquear_np else edit_np, "" if bloquear_ob else edit_ob, edit_valor, str(edit_data) if edit_status != "Pendente" else "", v_final, edit_status, id_editar))
                        conn.commit()
                        conn.close()
                        gerar_backup_csv()
                        st.success("Atualizado!")
                        st.rerun()

                st.write("---")
                st.subheader("❌ Exclusão de Registro")
                confirmar_exclusao = st.checkbox("Confirmo que desejo apagar permanentemente esta linha.")
                if st.button("Remover Registro Definitivamente", type="primary", disabled=not confirmar_exclusao):
                    conn = sqlite3.connect(DB_NAME)
                    conn.execute("DELETE FROM documentos WHERE id=?", (id_editar,))
                    conn.commit()
                    conn.close()
                    gerar_backup_csv()
                    st.success("Removido com sucesso!")
                    st.rerun()

    # 4. ABA DE AUDITORIA (VISUALIZAÇÃO COMPARTILHADA COMPLETA)
    with aba_backup:
        st.header("Reservas e Auditoria")
        conn = sqlite3.connect(DB_NAME)
        df_total = pd.read_sql_query("SELECT * FROM documentos", conn)
        conn.close()
        if not df_total.empty:
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1: busca_nf = st.text_input("Filtrar por NF:")
            with f_col2: busca_empresa = st.selectbox("Filtrar por Empresa:", ["TODAS"] + sorted(list(df_total['EMPRESA'].unique())))
            with f_col3: busca_status = st.selectbox("Filtrar por Status:", ["TODOS", "Pendente", "Liquidado", "Pago"])
            
            df_f = df_total.copy()
            if busca_nf: df_f = df_f[df_f['NF'].astype(str).str.contains(busca_nf, case=False)]
            if busca_empresa != "TODAS": df_f = df_f[df_f['EMPRESA'] == busca_empresa]
            if busca_status != "TODOS": df_f = df_f[df_f['STATUS'] == busca_status]
            
            df_v = df_f.copy()
            df_v['VALOR'] = df_v['VALOR'].apply(formatar_real)
            df_v['DATA'] = df_v['DATA'].apply(formatar_data_br)
            
            # Correção definitiva do final .0 no ano da tabela
            df_v['ANO'] = df_v['ANO'].astype(str).apply(lambda x: x.split('.')[0])
            
            st.dataframe(df_v, use_container_width=True)
            st.download_button("📥 Baixar Filtro (.CSV)", data=df_f.to_csv(index=False).encode('utf-8'), file_name="auditoria.csv", mime="text/csv")

    # 5. ABA DE CONFIGURAÇÕES (RESTRITA AO SCRG)
    with aba_config:
        st.header("Configurações Gerais")
        if not is_scrg:
            st.warning("⚠️ Apenas usuários do setor SCRG possuem autorização para alterar senhas ou militares.")
        
        st.subheader("🔑 Alterar Senha do Sistema")
        nova_s = st.text_input("Digite a Nova Senha:", type="password", disabled=not is_scrg)
        if st.button("Salvar Nova Senha", disabled=not is_scrg):
            if nova_s:
                st.session_state["senha_sistema"] = nova_s
                st.success("Senha alterada com sucesso!")
            else: st.error("Senha inválida.")
            
        st.write("---")
        st.subheader("🪖 Gerenciar Militares do Financeiro")
        c_ad, c_ex = st.columns(2)
        with c_ad:
            n_mil = st.text_input("Nome e Posto/Graduação:", disabled=not is_scrg).upper().strip()
            if st.button("➕ Cadastrar", disabled=not is_scrg):
                if n_mil:
                    try:
                        conn = sqlite3.connect(DB_NAME); conn.execute("INSERT INTO responsaveis (nome) VALUES (?)", (n_mil,)); conn.commit(); conn.close()
                        st.success("Cadastrado!"); st.rerun()
                    except: st.error("Já existe.")
        with c_ex:
            m_rem = st.selectbox("Militar para remover:", militares_cadastrados, disabled=not is_scrg)
            if st.button("❌ Remover", type="primary", disabled=not is_scrg):
                conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM responsaveis WHERE nome=?", (m_rem,)); conn.commit(); conn.close()
                st.success("Removido!"); st.rerun()

