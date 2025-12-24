from typing import List, Optional
from sqlmodel import Session, select, func
from models import Expense
import pandas as pd

def get_all_expenses(session: Session) -> List[Expense]:
    statement = select(Expense).order_by(Expense.date.desc())
    return session.exec(statement).all()

def create_expense(session: Session, description: str, amount_centavos: int, date: str, category: str = "Geral", paid: bool = True) -> Expense:
    expense = Expense(description=description, amount_centavos=amount_centavos, date=date, category=category, paid=paid)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense

def update_expense(session: Session, expense_id: int, **kwargs) -> Optional[Expense]:
    expense = session.get(Expense, expense_id)
    if not expense:
        return None
    for key, value in kwargs.items():
        setattr(expense, key, value)
    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense

def delete_expense(session: Session, expense_id: int):
    expense = session.get(Expense, expense_id)
    if expense:
        session.delete(expense)
        session.commit()

def get_total_expenses(session: Session) -> int:
    # Returns total paid expenses in centavos
    statement = select(func.sum(Expense.amount_centavos)).where(Expense.paid == True)
    return session.exec(statement).one() or 0

def get_expenses_by_month(session: Session) -> pd.DataFrame:
    query = select(Expense.date, Expense.amount_centavos).where(Expense.paid == True)
    data = session.exec(query).all()
    
    if not data:
        return pd.DataFrame(columns=["mes", "Despesas"])
        
    df = pd.DataFrame(data, columns=["date", "amount_centavos"])
    df["mes"] = df["date"].apply(lambda x: x[:7]) # YYYY-MM
    
    grouped = df.groupby("mes")["amount_centavos"].sum().reset_index()
    grouped["Despesas"] = grouped["amount_centavos"] / 100.0
    
    return grouped[["mes", "Despesas"]].sort_values("mes")
