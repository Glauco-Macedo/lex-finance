# app.py — LexFinance (Refactored)
# Programa simples, real, sem planilhas: controle financeiro por PROCESSO e por FASE
# Como rodar:
#   1) pip install -r requirements.txt
#   2) streamlit run app.py
# O banco de dados (SQLite) é criado automaticamente como 'lexfinance.db'.

import pandas as pd
import streamlit as st
from sqlmodel import Session
from datetime import date

from database import create_db_and_tables, engine
from services import client_service, process_service, finance_service, expense_service, report_service

########################
# CONFIG & INIT        #
########################
st.set_page_config(page_title="LexFinance — Controle por Processo", layout="wide")

# Initialize DB (safe to call multiple times)
create_db_and_tables()

st.title("LexFinance — Controle financeiro por processo (MVP)")
st.caption("Cada processo tem fases de pagamento condicionais. O faturamento do escritório é a soma do que entrou em payments.")

with st.sidebar:
    st.header("Navegação")
    page = st.radio("Ir para:", [
        "Painel",
        "Clientes",
        "Processos",
        "Fases & Recebimentos",
        "Despesas",
        "Relatórios",
        "Backup & Utilitários",
    ])

# Helper for formatting currency
def money(val: float) -> str:
    if val is None:
        val = 0
    return f"R$ {val/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Helper for cents conversion
def cents(val: float) -> int:
    if val is None:
        return 0
    return int(round(float(val) * 100))

# Open Session for the whole run
with Session(engine) as session:

    ########################
    # PÁGINA: PAINEL        #
    ########################
    if page == "Painel":
        st.subheader("Visão geral")

        # KPIs globais
        total_contratado, total_recebido, saldo_receber = finance_service.get_global_financials(session)
        total_despesas = expense_service.get_total_expenses(session)
        
        # Saldo Real = Recebido - Despesas
        saldo_real = total_recebido - total_despesas
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Contratado", money(total_contratado))
        col2.metric("Receita Realizada", money(total_recebido))
        col3.metric("Despesas Pagas", money(total_despesas))
        col4.metric("Lucro/Prejuízo (Caixa)", money(saldo_real), delta_color="normal")

        st.markdown("---")

        st.subheader("Fluxo de Caixa (Mensal)")
        
        # Get dataframes
        df_rec = finance_service.get_firm_revenue_by_month(session)
        df_exp = expense_service.get_expenses_by_month(session)
        
        if df_rec.empty and df_exp.empty:
            st.info("Sem movimentações financeiras ainda.")
        else:
            # Merge dataframes on 'mes'
            if df_rec.empty:
                df_rec = pd.DataFrame(columns=["mes", "Recebido"])
            if df_exp.empty:
                df_exp = pd.DataFrame(columns=["mes", "Despesas"])
                
            df_merged = pd.merge(df_rec, df_exp, on="mes", how="outer").fillna(0)
            df_merged = df_merged.sort_values("mes")
            df_merged["Saldo"] = df_merged["Recebido"] - df_merged["Despesas"]
            
            st.dataframe(df_merged, use_container_width=True)
            
            # Chart
            st.bar_chart(df_merged.set_index("mes")[["Recebido", "Despesas", "Saldo"]])

        st.markdown("---")
        st.subheader("Processos com saldo a receber")
        
        # Get all processes and calculate financials
        processes = process_service.get_all_processes(session)
        
        if not processes:
            st.warning("Cadastre clientes e processos para começar.")
        else:
            data = []
            for p in processes:
                tot, rec, sal, pct = finance_service.get_process_financials(session, p.id)
                # Access client name safely
                client_name = p.client.name if p.client else "N/A"
                
                data.append({
                    "ProcessoID": p.id,
                    "Cliente": client_name,
                    "Processo": p.title,
                    "Responsavel": p.responsible,
                    "Status": p.status,
                    "TotalContrato": tot/100,
                    "Recebido": rec/100,
                    "Saldo": sal/100,
                    "% Recebido": round(pct*100, 2)
                })
            
            df_proc = pd.DataFrame(data)
            # Sort by Client then Process
            if not df_proc.empty:
                df_proc = df_proc.sort_values(by=["Cliente", "Processo"])
                st.dataframe(df_proc, use_container_width=True)

    ########################
    # PÁGINA: CLIENTES      #
    ########################
    elif page == "Clientes":
        st.subheader("Clientes")
        with st.form("novo_cliente"):
            st.markdown("**Cadastrar/Atualizar Cliente**")
            name = st.text_input("Nome *")
            cpf = st.text_input("CPF/CNPJ")
            email = st.text_input("E-mail")
            phone = st.text_input("Telefone")
            submitted = st.form_submit_button("Salvar")
            
            if submitted and name.strip():
                client_service.create_client(session, name.strip(), cpf.strip(), email.strip(), phone.strip())
                st.success("Cliente salvo.")

        st.markdown("---")
        clients = client_service.get_all_clients(session)
        if clients:
            # Convert to DataFrame for display
            df = pd.DataFrame([c.model_dump() for c in clients])
            st.dataframe(df[["id", "name", "cpf_cnpj", "email", "phone"]], use_container_width=True)
            
            # Report Generation
            st.markdown("### Relatórios")
            client_opts = [f"{c.name} (ID: {c.id})" for c in clients]
            client_map_rep = {f"{c.name} (ID: {c.id})": c.id for c in clients}
            
            sel_cli_rep = st.selectbox("Selecione o cliente para gerar relatório", client_opts)
            
            if st.button("Gerar Relatório PDF"):
                cid = client_map_rep[sel_cli_rep]
                client_obj = session.get(client_service.Client, cid)
                
                # Gather data
                procs = process_service.get_processes_by_client(session, cid)
                
                # Calculate financials for this client
                # We can reuse get_process_financials for each process and sum up
                tot_c, tot_r, bal_c = 0, 0, 0
                for p in procs:
                    t, r, b, _ = finance_service.get_process_financials(session, p.id)
                    tot_c += t
                    tot_r += r
                    bal_c += b
                
                fins = {
                    'total_contracted': tot_c,
                    'total_received': tot_r,
                    'balance': bal_c
                }
                
                # Generate PDF
                pdf_file = report_service.generate_client_report(client_obj, procs, fins)
                
                with open(pdf_file, "rb") as f:
                    pdf_data = f.read()
                
                st.download_button(
                    label="Baixar PDF",
                    data=pdf_data,
                    file_name=pdf_file,
                    mime="application/pdf"
                )
                st.success(f"Relatório gerado: {pdf_file}")
            
            st.markdown("---")
            st.markdown("### Editar / Excluir Cliente")
            
            # Reuse client options from report section
            sel_cli_edit = st.selectbox("Selecione o cliente para editar/excluir", client_opts)
            cid_edit = client_map_rep[sel_cli_edit]
            
            # Get current object
            cli_obj = session.get(client_service.Client, cid_edit)
            
            with st.form("edit_client"):
                n_name = st.text_input("Nome", value=cli_obj.name)
                n_cpf = st.text_input("CPF/CNPJ", value=cli_obj.cpf_cnpj or "")
                n_email = st.text_input("E-mail", value=cli_obj.email or "")
                n_phone = st.text_input("Telefone", value=cli_obj.phone or "")
                
                c1, c2 = st.columns(2)
                save_c = c1.form_submit_button("Salvar Alterações")
                del_c = c2.form_submit_button("Excluir Cliente")
                
            if save_c:
                if n_name.strip():
                    client_service.update_client(
                        session, 
                        cid_edit, 
                        name=n_name.strip(), 
                        cpf_cnpj=n_cpf.strip(), 
                        email=n_email.strip(), 
                        phone=n_phone.strip()
                    )
                    st.success("Cliente atualizado.")
                    st.rerun()
                else:
                    st.error("O nome do cliente é obrigatório.")
                    
            if del_c:
                # Check for dependencies? 
                # Models have cascade delete, so processes will be deleted.
                # We should warn the user.
                st.warning("Atenção: Excluir um cliente apagará TODOS os seus processos, fases e pagamentos.")
                if st.button("Confirmar Exclusão do Cliente"):
                    client_service.delete_client(session, cid_edit)
                    st.success("Cliente excluído.")
                    st.rerun()
                
        else:
            st.info("Nenhum cliente cadastrado.")

    ########################
    # PÁGINA: PROCESSOS     #
    ########################
    elif page == "Processos":
        st.subheader("Processos")
        
        clients = client_service.get_all_clients(session)
        client_map = {c.name: c.id for c in clients}
        
        if not client_map:
            st.info("Cadastre um cliente primeiro.")
        else:
            with st.form("novo_processo"):
                st.markdown("**Cadastrar Processo**")
                cliente_nome = st.selectbox("Cliente *", list(client_map.keys()))
                cnj = st.text_input("Número CNJ")
                title = st.text_input("Título do processo *", placeholder="Ex.: Defesa Penal — Caso X")
                responsible = st.text_input("Responsável", value="Glauco")
                status = st.selectbox("Status", ["Ativo", "Encerrado", "Suspenso"], index=0)
                notes = st.text_area("Observações")
                ok = st.form_submit_button("Salvar")
                
                if ok and title.strip():
                    process_service.create_process(
                        session, 
                        client_id=client_map[cliente_nome], 
                        title=title.strip(), 
                        cnj=cnj.strip(), 
                        responsible=responsible.strip(), 
                        status=status, 
                        notes=notes.strip()
                    )
                    st.success("Processo salvo.")

        st.markdown("---")
        
        processes = process_service.get_all_processes(session)
        if processes:
            # Flatten data for display
            data = []
            for p in processes:
                data.append({
                    "ProcessoID": p.id,
                    "Cliente": p.client.name if p.client else "N/A",
                    "Processo": p.title,
                    "CNJ": p.cnj,
                    "Responsavel": p.responsible,
                    "Status": p.status,
                    "Observacoes": p.notes
                })
            dfp = pd.DataFrame(data)
            st.dataframe(dfp, use_container_width=True)
            
            # =========================
            # Editar / Mover / Excluir Processo
            # =========================
            st.markdown("### Editar / Mover / Excluir Processo")
            proc_opts = [f"#{row['ProcessoID']} — {row['Processo']} (Cliente: {row['Cliente']})" for _, row in dfp.iterrows()]
            proc_id_map = {label: int(row['ProcessoID']) for label, (_, row) in zip(proc_opts, dfp.iterrows())}
            
            sel_proc_label = st.selectbox("Escolha o processo", proc_opts)
            sel_proc_id = proc_id_map[sel_proc_label]

            with st.expander("Mover processo para outro cliente"):
                novo_cliente = st.selectbox("Novo cliente", list(client_map.keys()), key="move_proc")
                if st.button("Mover processo"):
                    process_service.update_process(session, sel_proc_id, client_id=client_map[novo_cliente])
                    st.success("Processo movido para o cliente selecionado.")
                    st.rerun()

            with st.expander("Excluir processo (apaga fases e recebimentos deste processo)"):
                st.warning("Atenção: a exclusão é definitiva. Fases e recebimentos vinculados serão removidos.")
                confirm = st.checkbox("Confirmo que desejo excluir este processo.")
                if st.button("Excluir processo"):
                    if confirm:
                        process_service.delete_process(session, sel_proc_id)
                        st.success("Processo excluído com sucesso.")
                        st.rerun()
                    else:
                        st.info("Marque a caixa de confirmação para excluir.")
        else:
            st.info("Nenhum processo cadastrado.")

    ###############################
    # PÁGINA: FASES & RECEBIMENTOS #
    ###############################
    elif page == "Fases & Recebimentos":
        st.subheader("Fases de Pagamento & Recebimentos")
        
        clients = client_service.get_all_clients(session)
        client_map = {c.name: c.id for c in clients}
        
        sel_client = st.selectbox("Filtrar por cliente (opcional)", ["(Todos)"] + list(client_map.keys()))
        
        if sel_client != "(Todos)":
            processes = process_service.get_processes_by_client(session, client_map[sel_client])
        else:
            processes = process_service.get_all_processes(session)
            
        pid_map = {p.title: p.id for p in processes}
        
        if not pid_map:
            st.info("Cadastre um processo primeiro.")
        else:
            sel_proc_name = st.selectbox("Processo *", list(pid_map.keys()))
            sel_proc_id = pid_map[sel_proc_name]

            # =========================
            # CRUD de FASES
            # =========================
            st.markdown("### Adicionar Fase")
            with st.form("add_fase"):
                description = st.text_input("Descrição da fase *", placeholder="Ex.: Inquérito Policial")
                condition = st.text_input("Condição (opcional)", placeholder="Ex.: Assinatura do contrato")
                value = st.number_input("Valor da fase (R$) *", min_value=0.0, step=100.0)
                ok = st.form_submit_button("Salvar fase")
                
                if ok and description.strip() and value > 0:
                    process_service.create_phase(
                        session, 
                        process_id=sel_proc_id, 
                        description=description.strip(), 
                        value_centavos=cents(value), 
                        condition=condition.strip()
                    )
                    st.success("Fase adicionada.")

            st.markdown("### Editar / Excluir Fase")
            phases = process_service.get_phases_by_process(session, sel_proc_id)
            
            if not phases:
                st.info("Nenhuma fase cadastrada para este processo.")
            else:
                fase_opts = [f"#{p.id} — {p.description} (previsto {money(p.value_centavos)})" for p in phases]
                fase_map = {label: p.id for label, p in zip(fase_opts, phases)}
                
                sel_fase_label = st.selectbox("Escolha a fase para gerenciar", fase_opts)
                sel_fase_id = fase_map[sel_fase_label]
                
                # Find the selected phase object
                fase_row = next(p for p in phases if p.id == sel_fase_id)

                with st.form("edit_fase"):
                    new_desc = st.text_input("Descrição", value=fase_row.description)
                    new_cond = st.text_input("Condição", value=fase_row.condition or "")
                    new_val = st.number_input("Valor previsto (R$)", min_value=0.0, value=float(fase_row.value_centavos/100), step=100.0)
                    c1, c2 = st.columns(2)
                    save_fase = c1.form_submit_button("Salvar alterações")
                    del_fase = c2.form_submit_button("Excluir fase")
                
                if save_fase:
                    process_service.update_phase(
                        session, 
                        sel_fase_id, 
                        description=new_desc.strip(), 
                        condition=new_cond.strip(), 
                        value_centavos=cents(new_val)
                    )
                    st.success("Fase atualizada.")
                    st.rerun()
                    
                if del_fase:
                    process_service.delete_phase(session, sel_fase_id)
                    st.success("Fase excluída.")
                    st.rerun()

            st.markdown("---")

            # =========================
            # CRUD de RECEBIMENTOS
            # =========================
            st.markdown("### Registrar Recebimento")
            # Refresh phases in case of updates
            phases = process_service.get_phases_by_process(session, sel_proc_id)
            
            if not phases:
                st.info("Adicione ao menos uma fase para registrar recebimento.")
            else:
                fase_labels = [f"#{p.id} — {p.description} (previsto {money(p.value_centavos)})" for p in phases]
                fase_id_map = {label: p.id for label, p in zip(fase_labels, phases)}
                
                with st.form("add_pay"):
                    fase_label = st.selectbox("Fase *", list(fase_id_map.keys()))
                    amount = st.number_input("Valor recebido (R$) *", min_value=0.0, step=100.0)
                    rdate = st.date_input("Data do recebimento *", value=date.today())
                    okp = st.form_submit_button("Registrar")
                    
                    if okp and amount > 0:
                        finance_service.create_payment(
                            session, 
                            phase_id=fase_id_map[fase_label], 
                            amount_centavos=cents(amount), 
                            received_date=rdate.isoformat()
                        )
                        st.success("Recebimento registrado.")

            st.markdown("### Editar / Excluir Recebimento")
            payments_data = finance_service.get_payments_by_process(session, sel_proc_id)
            
            if not payments_data:
                st.info("Nenhum recebimento registrado para este processo.")
            else:
                # payments_data is list of (Payment, Phase)
                pay_opts = []
                pay_map = {}
                
                for pay, ph in payments_data:
                    label = f"#{pay.id} — {ph.description} — {money(pay.amount_centavos)} em {pay.received_date}"
                    pay_opts.append(label)
                    pay_map[label] = pay
                
                sel_pay_label = st.selectbox("Escolha o recebimento para gerenciar", pay_opts)
                prow = pay_map[sel_pay_label]

                with st.form("edit_pay"):
                    new_amount = st.number_input("Valor recebido (R$)", min_value=0.0, value=float(prow.amount_centavos/100), step=100.0)
                    new_date = st.date_input("Data do recebimento", value=pd.to_datetime(prow.received_date).date())
                    c1, c2 = st.columns(2)
                    save_pay = c1.form_submit_button("Salvar alterações")
                    del_pay = c2.form_submit_button("Excluir recebimento")
                
                if save_pay:
                    finance_service.update_payment(
                        session, 
                        prow.id, 
                        amount_centavos=cents(new_amount), 
                        received_date=new_date.isoformat()
                    )
                    st.success("Recebimento atualizado.")
                    st.rerun()
                    
                if del_pay:
                    finance_service.delete_payment(session, prow.id)
                    st.success("Recebimento excluído.")
                    st.rerun()

            st.markdown("---")
            st.markdown("### Fases do processo selecionado")
            
            # Build dataframe for phases with received amounts
            # We need to query payments for each phase or do a smart join. 
            # For MVP, simple iteration is fine or we can add a service method.
            # Let's do iteration here for simplicity as we already have phases.
            
            phase_data = []
            for ph in phases:
                # Calculate received for this phase
                # This is a bit inefficient (N+1), but OK for MVP scale. 
                # Better would be a service method `get_phases_with_totals`.
                # Let's use what we have.
                pay_sum = sum(p.amount_centavos for p in ph.payments) # Relationship access
                
                phase_data.append({
                    "FaseID": ph.id,
                    "Fase": ph.description,
                    "Condicao": ph.condition,
                    "ValorPrevisto": ph.value_centavos / 100,
                    "Recebido": pay_sum / 100,
                    "SaldoFase": (ph.value_centavos - pay_sum) / 100
                })
            
            dff = pd.DataFrame(phase_data)
            st.dataframe(dff, use_container_width=True)

            st.markdown("### Situação do processo")
            tot, rec, sal, pct = finance_service.get_process_financials(session, sel_proc_id)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Contrato (soma fases)", money(tot))
            c2.metric("Recebido", money(rec))
            c3.metric("Saldo", money(sal))
            c4.metric("% Recebido", f"{pct*100:.1f}%")

    ########################
    # PÁGINA: DESPESAS      #
    ########################
    elif page == "Despesas":
        st.subheader("Controle de Despesas")
        
        with st.form("nova_despesa"):
            st.markdown("**Registrar Despesa**")
            desc = st.text_input("Descrição *", placeholder="Ex.: Aluguel, Software, Material")
            amount = st.number_input("Valor (R$) *", min_value=0.0, step=10.0)
            dt_exp = st.date_input("Data *", value=date.today())
            cat = st.selectbox("Categoria", ["Geral", "Pessoal", "Infraestrutura", "Marketing", "Tributos"])
            paid = st.checkbox("Pago?", value=True)
            
            sub = st.form_submit_button("Salvar Despesa")
            
            if sub and desc.strip() and amount > 0:
                expense_service.create_expense(
                    session,
                    description=desc.strip(),
                    amount_centavos=cents(amount),
                    date=dt_exp.isoformat(),
                    category=cat,
                    paid=paid
                )
                st.success("Despesa registrada.")
        
        st.markdown("---")
        st.markdown("### Histórico de Despesas")
        
        expenses = expense_service.get_all_expenses(session)
        if expenses:
            data = []
            for e in expenses:
                data.append({
                    "ID": e.id,
                    "Data": e.date,
                    "Descrição": e.description,
                    "Categoria": e.category,
                    "Valor": e.amount_centavos / 100,
                    "Pago": "Sim" if e.paid else "Não"
                })
            df_exp = pd.DataFrame(data)
            st.dataframe(df_exp, use_container_width=True)
            
            # Edit/Delete
            st.markdown("### Editar / Excluir")
            exp_opts = [f"#{row['ID']} — {row['Descrição']} ({money(row['Valor']*100)})" for row in data]
            exp_map = {label: row['ID'] for label, row in zip(exp_opts, data)}
            
            sel_exp_label = st.selectbox("Selecione a despesa", exp_opts)
            sel_exp_id = exp_map[sel_exp_label]
            
            # Get object
            exp_obj = next(e for e in expenses if e.id == sel_exp_id)
            
            with st.form("edit_exp"):
                n_desc = st.text_input("Descrição", value=exp_obj.description)
                n_val = st.number_input("Valor (R$)", min_value=0.0, value=float(exp_obj.amount_centavos/100), step=10.0)
                n_date = st.date_input("Data", value=pd.to_datetime(exp_obj.date).date())
                n_cat = st.selectbox("Categoria", ["Geral", "Pessoal", "Infraestrutura", "Marketing", "Tributos"], index=["Geral", "Pessoal", "Infraestrutura", "Marketing", "Tributos"].index(exp_obj.category) if exp_obj.category in ["Geral", "Pessoal", "Infraestrutura", "Marketing", "Tributos"] else 0)
                n_paid = st.checkbox("Pago?", value=exp_obj.paid)
                
                c1, c2 = st.columns(2)
                save_e = c1.form_submit_button("Salvar Alterações")
                del_e = c2.form_submit_button("Excluir Despesa")
                
            if save_e:
                expense_service.update_expense(
                    session,
                    sel_exp_id,
                    description=n_desc.strip(),
                    amount_centavos=cents(n_val),
                    date=n_date.isoformat(),
                    category=n_cat,
                    paid=n_paid
                )
                st.success("Despesa atualizada.")
                st.rerun()
                
            if del_e:
                expense_service.delete_expense(session, sel_exp_id)
                st.success("Despesa excluída.")
                st.rerun()
                
        else:
            st.info("Nenhuma despesa registrada.")

    ########################
    # PÁGINA: RELATÓRIOS    #
    ########################
    elif page == "Relatórios":
        st.subheader("Relatórios")
        resp = st.text_input("Filtrar por responsável (opcional)")
        
        # Get all processes
        processes = process_service.get_all_processes(session)
        
        # Filter in Python (easier than dynamic SQL construction for MVP)
        if resp.strip():
            processes = [p for p in processes if p.responsible and resp.strip().lower() in p.responsible.lower()]
            
        data = []
        for p in processes:
            tot, rec, sal, pct = finance_service.get_process_financials(session, p.id)
            data.append({
                "ProcessoID": p.id,
                "Cliente": p.client.name if p.client else "N/A",
                "Processo": p.title,
                "Responsavel": p.responsible,
                "TotalContrato": tot/100,
                "Recebido": rec/100,
                "Saldo": sal/100,
                "% Recebido": round(pct*100, 2)
            })
            
        dfr = pd.DataFrame(data)
        if not dfr.empty:
            dfr = dfr.sort_values(by=["Cliente", "Processo"])
            st.dataframe(dfr, use_container_width=True)
        else:
            st.info("Nenhum processo encontrado.")

    ###############################
    # PÁGINA: BACKUP & UTILITÁRIOS #
    ###############################
    elif page == "Backup & Utilitários":
        st.subheader("Backup & Utilitários")
        st.markdown("Faça backup dos dados localmente (CSV) para evitar perda.")

        if st.button("Exportar CSVs"):
            # Use pandas read_sql with the engine
            df_clients = pd.read_sql("SELECT * FROM clients", engine)
            df_processes = pd.read_sql("SELECT * FROM processes", engine)
            df_phases = pd.read_sql("SELECT * FROM phases", engine)
            df_payments = pd.read_sql("SELECT * FROM payments", engine)

            df_clients.to_csv("clients.csv", index=False)
            df_processes.to_csv("processes.csv", index=False)
            df_phases.to_csv("phases.csv", index=False)
            df_payments.to_csv("payments.csv", index=False)
            st.success("Arquivos CSV gerados na pasta atual do app.")

        st.info("Para backup do banco inteiro, copie o arquivo 'lexfinance.db'.")

    st.caption("© 2025 — LexFinance MVP. Banco: SQLite (via SQLModel).")