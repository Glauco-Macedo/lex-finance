from typing import List, Optional
from sqlmodel import Session, select
from models import Client

def get_all_clients(session: Session) -> List[Client]:
    statement = select(Client).order_by(Client.name)
    return session.exec(statement).all()

def create_client(session: Session, name: str, cpf_cnpj: Optional[str], email: Optional[str], phone: Optional[str]) -> Client:
    client = Client(name=name, cpf_cnpj=cpf_cnpj, email=email, phone=phone)
    session.add(client)
    session.commit()
    session.refresh(client)
    return client

def update_client(session: Session, client_id: int, **kwargs) -> Optional[Client]:
    client = session.get(Client, client_id)
    if not client:
        return None
    for key, value in kwargs.items():
        setattr(client, key, value)
    session.add(client)
    session.commit()
    session.refresh(client)
    session.refresh(client)
    return client

def delete_client(session: Session, client_id: int):
    client = session.get(Client, client_id)
    if client:
        session.delete(client)
        session.commit()
