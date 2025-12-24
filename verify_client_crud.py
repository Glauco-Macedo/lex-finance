from sqlmodel import Session
from database import create_db_and_tables, engine
from services import client_service

def verify_client_crud():
    print("Initializing DB...")
    create_db_and_tables()
    
    with Session(engine) as session:
        print("Creating Client...")
        client = client_service.create_client(session, "CRUD Client", "111", "crud@test.com", "111")
        cid = client.id
        print(f"Client created: {client.name} (ID: {cid})")
        
        print("Updating Client...")
        updated = client_service.update_client(session, cid, name="Updated Client", email="updated@test.com")
        print(f"Client updated: {updated.name}, {updated.email}")
        
        assert updated.name == "Updated Client"
        assert updated.email == "updated@test.com"
        
        print("Deleting Client...")
        client_service.delete_client(session, cid)
        
        check = session.get(client_service.Client, cid)
        assert check is None
        print("Client deleted successfully.")
            
    print("Verification Successful!")

if __name__ == "__main__":
    verify_client_crud()
