import streamlit as st
from database import create_db_and_tables
from ui.dashboard import show_dashboard
from ui.clients import show_clients
from ui.processes import show_processes
from ui.finance import show_finance
from ui.reports import show_reports
from ui.backup import show_backup

# Initialize DB
create_db_and_tables()

st.set_page_config(page_title="LexFinance", layout="wide")

st.title("LexFinance 2.0")

with st.sidebar:
    st.header("Navegação")
    page = st.radio("Ir para:", [
        "Painel",
        "Clientes",
        "Processos",
        "Fases & Recebimentos",
        "Relatórios",
        "Backup"
    ])

if page == "Painel":
    show_dashboard()
elif page == "Clientes":
    show_clients()
elif page == "Processos":
    show_processes()
elif page == "Fases & Recebimentos":
    show_finance()
elif page == "Relatórios":
    show_reports()
elif page == "Backup":
    show_backup()
