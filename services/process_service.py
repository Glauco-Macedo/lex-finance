from typing import List, Optional
from sqlmodel import Session, select
from models import Process, Phase

# --- Process Operations ---
def get_processes_by_client(session: Session, client_id: int) -> List[Process]:
    statement = select(Process).where(Process.client_id == client_id).order_by(Process.title)
    return session.exec(statement).all()

def get_all_processes(session: Session) -> List[Process]:
    statement = select(Process).order_by(Process.title)
    return session.exec(statement).all()

def create_process(session: Session, client_id: int, title: str, cnj: str = None, responsible: str = None, status: str = "Ativo", notes: str = None) -> Process:
    process = Process(client_id=client_id, title=title, cnj=cnj, responsible=responsible, status=status, notes=notes)
    session.add(process)
    session.commit()
    session.refresh(process)
    return process

def update_process(session: Session, process_id: int, **kwargs) -> Optional[Process]:
    process = session.get(Process, process_id)
    if not process:
        return None
    for key, value in kwargs.items():
        setattr(process, key, value)
    session.add(process)
    session.commit()
    session.refresh(process)
    return process

def delete_process(session: Session, process_id: int):
    process = session.get(Process, process_id)
    if process:
        session.delete(process)
        session.commit()

# --- Phase Operations ---
def get_phases_by_process(session: Session, process_id: int) -> List[Phase]:
    statement = select(Phase).where(Phase.process_id == process_id).order_by(Phase.id)
    return session.exec(statement).all()

def create_phase(session: Session, process_id: int, description: str, value_centavos: int, condition: str = None) -> Phase:
    phase = Phase(process_id=process_id, description=description, value_centavos=value_centavos, condition=condition)
    session.add(phase)
    session.commit()
    session.refresh(phase)
    return phase

def update_phase(session: Session, phase_id: int, **kwargs) -> Optional[Phase]:
    phase = session.get(Phase, phase_id)
    if not phase:
        return None
    for key, value in kwargs.items():
        setattr(phase, key, value)
    session.add(phase)
    session.commit()
    session.refresh(phase)
    return phase

def delete_phase(session: Session, phase_id: int):
    phase = session.get(Phase, phase_id)
    if phase:
        session.delete(phase)
        session.commit()
