from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Observacao:
    """Um valor de um indicador numa data. Para série mensal, o dia 1 do mês."""

    data: date
    valor: Decimal
