import streamlit as st
import pandas as pd
from database import get_session
from models import Client, Process, Phase, Payment
from sqlmodel import select

def show_backup():
    st.subheader("Backup & Exportação")
    
    if st.button("Gerar CSVs"):
        with next(get_session()) as session:
            clients = session.exec(select(Client)).all()
            processes = session.exec(select(Process)).all()
            phases = session.exec(select(Phase)).all()
            payments = session.exec(select(Payment)).all()
            
            pd.DataFrame([c.model_dump() for c in clients]).to_csv("clients.csv", index=False)
            pd.DataFrame([p.model_dump() for p in processes]).to_csv("processes.csv", index=False)
            pd.DataFrame([ph.model_dump() for ph in phases]).to_csv("phases.csv", index=False)
            pd.DataFrame([pay.model_dump() for pay in payments]).to_csv("payments.csv", index=False)
            
            st.success("Arquivos CSV gerados na pasta do projeto.")
