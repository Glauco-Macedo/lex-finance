from typing import List, Optional, Tuple
from sqlmodel import Session, select, func
from models import Payment, Phase, Process
import pandas as pd

# --- Payment Operations ---
def get_payments_by_process(session: Session, process_id: int) -> List[Tuple[Payment, Phase]]:
    # Join Payment and Phase to filter by process_id
    statement = select(Payment, Phase).join(Phase).where(Phase.process_id == process_id).order_by(Payment.received_date.desc())
    results = session.exec(statement).all()
    return results # Returns list of (Payment, Phase) tuples

def create_payment(session: Session, phase_id: int, amount_centavos: int, received_date: str) -> Payment:
    payment = Payment(phase_id=phase_id, amount_centavos=amount_centavos, received_date=received_date)
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment

def update_payment(session: Session, payment_id: int, **kwargs) -> Optional[Payment]:
    payment = session.get(Payment, payment_id)
    if not payment:
        return None
    for key, value in kwargs.items():
        setattr(payment, key, value)
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment

def delete_payment(session: Session, payment_id: int):
    payment = session.get(Payment, payment_id)
    if payment:
        session.delete(payment)
        session.commit()

# --- Financial Calculations ---
def get_process_financials(session: Session, process_id: int) -> Tuple[int, int, int, float]:
    """
    Returns (total_contracted, total_received, balance, percentage_received)
    All monetary values in centavos.
    """
    # Total Contracted
    total_contracted = session.exec(
        select(func.sum(Phase.value_centavos)).where(Phase.process_id == process_id)
    ).one() or 0
    
    # Total Received
    total_received = session.exec(
        select(func.sum(Payment.amount_centavos))
        .join(Phase)
        .where(Phase.process_id == process_id)
    ).one() or 0
    
    balance = total_contracted - total_received
    pct = (total_received / total_contracted) if total_contracted > 0 else 0.0
    
    return total_contracted, total_received, balance, pct

def get_firm_revenue_by_month(session: Session) -> pd.DataFrame:
    # Using pandas for aggregation as in original app, but fetching raw data first or using SQL
    # SQLModel doesn't support complex date functions across all DBs easily, but SQLite has substr
    
    query = select(Payment.received_date, Payment.amount_centavos)
    data = session.exec(query).all()
    
    if not data:
        return pd.DataFrame(columns=["mes", "Recebido"])
        
    df = pd.DataFrame(data, columns=["received_date", "amount_centavos"])
    df["mes"] = df["received_date"].apply(lambda x: x[:7]) # YYYY-MM
    
    grouped = df.groupby("mes")["amount_centavos"].sum().reset_index()
    grouped["Recebido"] = grouped["amount_centavos"] / 100.0
    
    return grouped[["mes", "Recebido"]].sort_values("mes")

def get_global_financials(session: Session) -> Tuple[int, int, int]:
    total_contracted = session.exec(select(func.sum(Phase.value_centavos))).one() or 0
    total_received = session.exec(select(func.sum(Payment.amount_centavos))).one() or 0
    balance = total_contracted - total_received
    return total_contracted, total_received, balance
