from sqlmodel import Session
from database import create_db_and_tables, engine
from services import client_service, process_service, finance_service, report_service
import os

def verify_report():
    print("Initializing DB...")
    create_db_and_tables()
    
    with Session(engine) as session:
        print("Creating Test Data...")
        client = client_service.create_client(session, "Report Client", "999", "rep@test.com", "999")
        proc = process_service.create_process(session, client.id, "Report Process")
        phase = process_service.create_phase(session, proc.id, "Phase 1", 100000)
        finance_service.create_payment(session, phase.id, 50000, "2025-02-01")
        
        # Reload to get relationships
        session.refresh(client)
        session.refresh(proc)
        
        # Prepare data for report
        procs = [proc] # In real app we fetch list
        
        # Financials
        tot, rec, bal, _ = finance_service.get_process_financials(session, proc.id)
        fins = {
            'total_contracted': tot,
            'total_received': rec,
            'balance': bal
        }
        
        print("Generating PDF...")
        filename = report_service.generate_client_report(client, procs, fins)
        print(f"PDF Generated: {filename}")
        
        assert os.path.exists(filename)
        assert filename.endswith(".pdf")
        
        print("Cleaning up...")
        process_service.delete_process(session, proc.id)
        # Client cleanup skipped for simplicity
        if os.path.exists(filename):
            os.remove(filename)
            print("PDF removed.")
            
    print("Verification Successful!")

if __name__ == "__main__":
    verify_report()
