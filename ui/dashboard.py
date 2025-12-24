import streamlit as st
from services.finance_service import get_global_financials, get_firm_revenue_by_month
from services.process_service import get_all_processes
from services.finance_service import get_process_financials
from ui.utils import money
from database import get_session
import pandas as pd

def show_dashboard():
    st.subheader("Visão geral")
    
    with next(get_session()) as session:
        # KPIs
        total_contratado, total_recebido, saldo = get_global_financials(session)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Contratado", money(total_contratado))
        col2.metric("Total Recebido", money(total_recebido))
        col3.metric("Saldo a Receber", money(saldo))
        
        st.markdown("---")
        
        # Revenue Chart
        st.subheader("Faturamento por mês (Entradas)")
        dfm = get_firm_revenue_by_month(session)
        if dfm.empty:
             st.info("Sem recebimentos ainda.")
        else:
            st.dataframe(dfm, use_container_width=True)
            st.bar_chart(dfm.set_index("mes")["Recebido"])
            
        st.markdown("---")
        
        # Processes with Balance
        st.subheader("Processos com saldo a receber")
        processes = get_all_processes(session)
        
        data = []
        for p in processes:
            tot, rec, sal, pct = get_process_financials(session, p.id)
            if sal > 0: # Only show if there is balance
                data.append({
                    "Cliente": p.client.name,
                    "Processo": p.title,
                    "Responsável": p.responsible,
                    "Status": p.status,
                    "Total Contrato": tot/100,
                    "Recebido": rec/100,
                    "Saldo": sal/100,
                    "% Recebido": round(pct*100, 2)
                })
        
        if not data:
             st.info("Nenhum processo com saldo pendente.")
        else:
            df_proc = pd.DataFrame(data)
            st.dataframe(df_proc, use_container_width=True)
