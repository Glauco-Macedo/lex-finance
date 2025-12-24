from fpdf import FPDF
from models import Client, Process, Phase, Payment
from typing import List, Tuple
import os

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Lex Finance - Relatório do Cliente', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

def generate_client_report(client: Client, processes: List[Process], financials: dict) -> str:
    """
    Generates a PDF report for a specific client.
    Returns the filename of the generated PDF.
    """
    pdf = PDFReport()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # --- Client Info ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Cliente: {client.name}', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    info_line = []
    if client.cpf_cnpj: info_line.append(f"CPF/CNPJ: {client.cpf_cnpj}")
    if client.email: info_line.append(f"Email: {client.email}")
    if client.phone: info_line.append(f"Tel: {client.phone}")
    
    if info_line:
        pdf.cell(0, 6, " | ".join(info_line), 0, 1)
    
    pdf.ln(5)
    
    # --- Financial Summary ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'Resumo Financeiro Global', 1, 1, 'L', fill=True)
    
    pdf.set_font('Arial', '', 10)
    # financials dict expected keys: 'total_contracted', 'total_received', 'balance' (all in centavos)
    tot = financials.get('total_contracted', 0) / 100
    rec = financials.get('total_received', 0) / 100
    bal = financials.get('balance', 0) / 100
    
    pdf.cell(63, 8, f"Total Contratado: R$ {tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 1)
    pdf.cell(63, 8, f"Total Pago: R$ {rec:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 1)
    pdf.cell(63, 8, f"Saldo Devedor: R$ {bal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 1)
    pdf.ln(10)
    
    # --- Processes ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Detalhamento dos Processos', 0, 1)
    
    if not processes:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, 'Nenhum processo cadastrado.', 0, 1)
    else:
        for proc in processes:
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(230, 230, 250) # Lavender
            title = f"Processo: {proc.title}"
            if proc.cnj:
                title += f" (CNJ: {proc.cnj})"
            pdf.cell(0, 8, title, 1, 1, 'L', fill=True)
            
            pdf.set_font('Arial', '', 9)
            pdf.multi_cell(0, 6, f"Status: {proc.status} | Responsável: {proc.responsible or 'N/A'}\nObs: {proc.notes or '-'}")
            
            # Phases table
            pdf.ln(2)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(80, 6, "Fase / Descrição", 1)
            pdf.cell(35, 6, "Valor (R$)", 1)
            pdf.cell(35, 6, "Recebido (R$)", 1)
            pdf.cell(40, 6, "Situação", 1, 1)
            
            pdf.set_font('Arial', '', 9)
            
            # We need to calculate phase totals here or pass them in.
            # For simplicity, we'll assume the caller might pass enriched objects or we calculate on the fly.
            # But since we are inside the service, we can't easily query DB if we just passed objects.
            # Ideally, this service should receive data structures ready for printing.
            # However, to keep it simple, let's assume 'proc' has 'phases' loaded and we sum payments.
            
            if not proc.phases:
                pdf.cell(190, 6, "Nenhuma fase cadastrada.", 1, 1, 'C')
            else:
                for phase in proc.phases:
                    val = phase.value_centavos / 100
                    
                    # Calculate received for this phase
                    rec_phase = sum(p.amount_centavos for p in phase.payments) / 100
                    
                    status = "Quitado" if rec_phase >= val and val > 0 else "Pendente"
                    if val == 0: status = "-"
                    if rec_phase > 0 and rec_phase < val: status = "Parcial"
                    
                    pdf.cell(80, 6, f"{phase.description}", 1)
                    pdf.cell(35, 6, f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 1)
                    pdf.cell(35, 6, f"{rec_phase:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), 1)
                    pdf.cell(40, 6, status, 1, 1)
            
            pdf.ln(5)
            
    # Output
    filename = f"Relatorio_{client.name.replace(' ', '_')}_{client.id}.pdf"
    # Sanitize filename
    filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '_')]).strip()
    pdf.output(filename)
    return filename
