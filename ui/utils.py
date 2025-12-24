from typing import Optional

def money(cents_val: Optional[int]) -> str:
    if cents_val is None:
        cents_val = 0
    return f"R$ {cents_val/100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def cents(n: Optional[float]) -> int:
    if n is None:
        return 0
    return int(round(float(n) * 100))
