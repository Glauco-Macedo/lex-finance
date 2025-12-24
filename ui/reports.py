import streamlit as st
from services.process_service import get_all_processes
from services.finance_service import get_process_financials
from database import get_session
import pandas as pd

def show_reports():
    st.subheader("Relatórios")
    
    with next(get_session()) as session:
        processes = get_all_processes(session)
        
        data = []
        for p in processes:
            tot, rec, sal, pct = get_process_financials(session, p.id)
            data.append({
                "Cliente": p.client.name,
                "Processo": p.title,
                "Responsável": p.responsible,
                "Total Contrato": tot/100,
                "Recebido": rec/100,
                "Saldo": sal/100,
                "% Recebido": round(pct*100, 2)
            })
            
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Sem dados para relatório.")
