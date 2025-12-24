from sqlmodel import Session, select
from database import create_db_and_tables, engine
from services import client_service, process_service, finance_service
from models import Client, Process, Phase, Payment
import os

def verify():
    print("Initializing DB...")
    create_db_and_tables()
    
    with Session(engine) as session:
        print("Creating Client...")
        client = client_service.create_client(session, "Test Client", "123", "test@test.com", "111")
        assert client.id is not None
        print(f"Client created: {client.name} (ID: {client.id})")
        
        print("Creating Process...")
        process = process_service.create_process(session, client.id, "Test Process")
        assert process.id is not None
        print(f"Process created: {process.title} (ID: {process.id})")
        
        print("Creating Phase...")
        phase = process_service.create_phase(session, process.id, "Test Phase", 100000) # R$ 1000.00
        assert phase.id is not None
        print(f"Phase created: {phase.description} (ID: {phase.id})")
        
        print("Creating Payment...")
        payment = finance_service.create_payment(session, phase.id, 50000, "2025-01-01") # R$ 500.00
        assert payment.id is not None
        print(f"Payment created: {payment.amount_centavos} (ID: {payment.id})")
        
        print("Checking Financials...")
        tot, rec, sal, pct = finance_service.get_process_financials(session, process.id)
        print(f"Total: {tot}, Received: {rec}, Balance: {sal}, %: {pct}")
        
        assert tot == 100000
        assert rec == 50000
        assert sal == 50000
        assert pct == 0.5
        
        print("Cleaning up...")
        process_service.delete_process(session, process.id)
        # Client cleanup if needed, but for test DB it's fine.
        
    print("Verification Successful!")

if __name__ == "__main__":
    if os.path.exists("lexfinance.db"):
        # Optional: remove existing db to test fresh start
        # os.remove("lexfinance.db")
        pass
    verify()
