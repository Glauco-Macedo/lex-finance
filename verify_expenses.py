from sqlmodel import Session
from database import create_db_and_tables, engine
from services import expense_service, finance_service
from datetime import date

def verify_expenses():
    print("Initializing DB...")
    create_db_and_tables()
    
    with Session(engine) as session:
        print("Creating Expenses...")
        # Create a paid expense
        exp1 = expense_service.create_expense(session, "Rent", 200000, "2025-01-10", "Infraestrutura", True) # R$ 2000.00
        # Create an unpaid expense (should not count towards total paid)
        exp2 = expense_service.create_expense(session, "Software", 50000, "2025-01-15", "Geral", False) # R$ 500.00
        
        print(f"Expense 1: {exp1.description}, Paid: {exp1.paid}")
        print(f"Expense 2: {exp2.description}, Paid: {exp2.paid}")
        
        print("Checking Total Expenses...")
        total_paid = expense_service.get_total_expenses(session)
        print(f"Total Paid Expenses: {total_paid}")
        
        assert total_paid == 200000
        
        print("Checking Monthly Aggregation...")
        df = expense_service.get_expenses_by_month(session)
        print(df)
        
        # Should have one entry for 2025-01 with 2000.00
        assert not df.empty
        assert df.iloc[0]["Despesas"] == 2000.00
        
        print("Cleaning up...")
        expense_service.delete_expense(session, exp1.id)
        expense_service.delete_expense(session, exp2.id)
        
    print("Verification Successful!")

if __name__ == "__main__":
    verify_expenses()
