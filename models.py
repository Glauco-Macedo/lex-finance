from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import date

class Client(SQLModel, table=True):
    __tablename__ = "clients"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    cpf_cnpj: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    processes: List["Process"] = Relationship(back_populates="client", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Process(SQLModel, table=True):
    __tablename__ = "processes"
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id") # Client deletion logic handled by Client.processes cascade or DB cascade if configured
    cnj: Optional[str] = None
    title: str
    responsible: Optional[str] = None
    status: str = Field(default="Ativo")
    notes: Optional[str] = None
    
    client: Client = Relationship(back_populates="processes")
    phases: List["Phase"] = Relationship(back_populates="process", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Phase(SQLModel, table=True):
    __tablename__ = "phases"
    id: Optional[int] = Field(default=None, primary_key=True)
    process_id: int = Field(foreign_key="processes.id") # We rely on Python side cascade from Process.phases for now, or existing DB schema
    description: str
    condition: Optional[str] = None
    value_centavos: int = Field(default=0)
    
    process: Process = Relationship(back_populates="phases")
    payments: List["Payment"] = Relationship(back_populates="phase", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    id: Optional[int] = Field(default=None, primary_key=True)
    phase_id: int = Field(foreign_key="phases.id")
    amount_centavos: int
    received_date: str # ISO format YYYY-MM-DD
    
    phase: Phase = Relationship(back_populates="payments")

class Expense(SQLModel, table=True):
    __tablename__ = "expenses"
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    amount_centavos: int
    date: str # ISO format YYYY-MM-DD
    category: Optional[str] = Field(default="Geral")
    paid: bool = Field(default=True)
