import streamlit as st
from services.client_service import create_client, get_all_clients
from database import get_session
import pandas as pd

def show_clients():
    st.subheader("Clientes")
    
    with next(get_session()) as session:
        with st.form("novo_cliente"):
            st.markdown("**Cadastrar Cliente**")
            name = st.text_input("Nome *")
            cpf = st.text_input("CPF/CNPJ")
            email = st.text_input("E-mail")
            phone = st.text_input("Telefone")
            submitted = st.form_submit_button("Salvar")
            
            if submitted and name.strip():
                create_client(session, name.strip(), cpf.strip(), email.strip(), phone.strip())
                st.success("Cliente salvo.")
                st.rerun()
        
        st.markdown("---")
        clients = get_all_clients(session)
        if clients:
            data = [{"ID": c.id, "Nome": c.name, "CPF/CNPJ": c.cpf_cnpj, "Email": c.email, "Telefone": c.phone} for c in clients]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("Nenhum cliente cadastrado.")
