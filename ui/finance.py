import streamlit as st
from services.client_service import get_all_clients
from services.process_service import get_processes_by_client, get_phases_by_process, create_phase, update_phase, delete_phase
from services.finance_service import get_payments_by_process, create_payment, update_payment, delete_payment, get_process_financials
from database import get_session
from ui.utils import money, cents
from datetime import date
import pandas as pd

def show_finance():
    st.subheader("Fases de Pagamento & Recebimentos")
    
    with next(get_session()) as session:
        clients = get_all_clients(session)
        client_options = {c.name: c.id for c in clients}
        
        sel_client_name = st.selectbox("Filtrar por cliente", ["(Todos)"] + list(client_options.keys()))
        
        if sel_client_name == "(Todos)":
            # This might be inefficient if many processes, but ok for MVP
            from services.process_service import get_all_processes
            processes = get_all_processes(session)
        else:
            processes = get_processes_by_client(session, client_options[sel_client_name])
            
        proc_map = {p.title: p.id for p in processes}
        
        if not proc_map:
            st.info("Nenhum processo encontrado.")
            return

        sel_proc_name = st.selectbox("Processo", list(proc_map.keys()))
        sel_proc_id = proc_map[sel_proc_name]
        
        # --- Phases CRUD ---
        st.markdown("### Adicionar Fase")
        with st.form("add_fase"):
            desc = st.text_input("Descrição *")
            cond = st.text_input("Condição")
            val = st.number_input("Valor (R$) *", min_value=0.0, step=100.0)
            if st.form_submit_button("Salvar Fase"):
                if desc and val > 0:
                    create_phase(session, sel_proc_id, desc, cents(val), cond)
                    st.success("Fase adicionada.")
                    st.rerun()

        st.markdown("### Gerenciar Fases")
        phases = get_phases_by_process(session, sel_proc_id)
        if phases:
            phase_opts = [f"#{ph.id} - {ph.description} ({money(ph.value_centavos)})" for ph in phases]
            phase_map = {label: ph.id for label, ph in zip(phase_opts, phases)}
            sel_phase_label = st.selectbox("Selecionar Fase", phase_opts)
            sel_phase_id = phase_map[sel_phase_label]
            
            c1, c2 = st.columns(2)
            if c1.button("Excluir Fase"):
                delete_phase(session, sel_phase_id)
                st.success("Fase excluída.")
                st.rerun()
        else:
            st.info("Nenhuma fase cadastrada.")

        st.markdown("---")
        
        # --- Payments CRUD ---
        st.markdown("### Registrar Recebimento")
        if phases:
            with st.form("add_pay"):
                p_phase_label = st.selectbox("Fase *", phase_opts)
                p_amount = st.number_input("Valor Recebido (R$) *", min_value=0.0, step=100.0)
                p_date = st.date_input("Data", value=date.today())
                
                if st.form_submit_button("Registrar"):
                    if p_amount > 0:
                        create_payment(session, phase_map[p_phase_label], cents(p_amount), p_date.isoformat())
                        st.success("Pagamento registrado.")
                        st.rerun()
        
        st.markdown("### Histórico de Recebimentos")
        payments_data = get_payments_by_process(session, sel_proc_id)
        if payments_data:
            # payments_data is list of (Payment, Phase)
            data = []
            for pay, ph in payments_data:
                data.append({
                    "ID": pay.id,
                    "Fase": ph.description,
                    "Valor": pay.amount_centavos/100,
                    "Data": pay.received_date
                })
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("Nenhum recebimento.")

        # --- Summary ---
        st.markdown("### Resumo do Processo")
        tot, rec, sal, pct = get_process_financials(session, sel_proc_id)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", money(tot))
        c2.metric("Recebido", money(rec))
        c3.metric("Saldo", money(sal))
        c4.metric("%", f"{pct*100:.1f}%")
