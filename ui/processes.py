import streamlit as st
from services.client_service import get_all_clients
from services.process_service import create_process, get_all_processes, update_process, delete_process
from database import get_session
import pandas as pd

def show_processes():
    st.subheader("Processos")
    
    with next(get_session()) as session:
        clients = get_all_clients(session)
        client_map = {c.name: c.id for c in clients}
        
        if not client_map:
            st.info("Cadastre um cliente primeiro.")
            return

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
                create_process(session, client_map[cliente_nome], title.strip(), cnj.strip(), responsible.strip(), status, notes.strip())
                st.success("Processo salvo.")
                st.rerun()

        st.markdown("---")
        processes = get_all_processes(session)
        
        if processes:
            data = [{
                "ID": p.id, 
                "Cliente": p.client.name, 
                "Processo": p.title, 
                "CNJ": p.cnj, 
                "Responsável": p.responsible, 
                "Status": p.status,
                "Obs": p.notes
            } for p in processes]
            dfp = pd.DataFrame(data)
            st.dataframe(dfp, use_container_width=True)
            
            # Edit/Delete
            st.markdown("### Gerenciar Processo")
            proc_opts = [f"#{p.id} — {p.title} ({p.client.name})" for p in processes]
            proc_map = {label: p.id for label, p in zip(proc_opts, processes)}
            
            sel_proc_label = st.selectbox("Escolha o processo", proc_opts)
            sel_proc_id = proc_map[sel_proc_label]
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Excluir Processo"):
                    delete_process(session, sel_proc_id)
                    st.success("Processo excluído.")
                    st.rerun()
        else:
            st.info("Nenhum processo cadastrado.")
