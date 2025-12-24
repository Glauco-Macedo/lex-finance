import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    print("Importing modules...")
    from database import create_db_and_tables, get_session
    from models import Client, Process
    from services.client_service import create_client, get_all_clients
    
    print("Creating DB...")
    create_db_and_tables()
    
    print("Testing Client Service...")
    with next(get_session()) as session:
        # Check if we can query (even if empty)
        clients = get_all_clients(session)
        print(f"Clients found: {len(clients)}")
        
    print("Verification Successful!")
except Exception as e:
    print(f"Verification Failed: {e}")
    import traceback
    traceback.print_exc()
