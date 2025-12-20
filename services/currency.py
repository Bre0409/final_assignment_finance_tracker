from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, Tuple

import requests
from django.core.cache import cache


FRANKFURTER_LATEST = "https://api.frankfurter.dev/latest"


@dataclass(frozen=True)
class RatesResult:
    base: str
    date: str
    rates: Dict[str, Decimal]


def get_latest_rates(base: str = "EUR", symbols: Iterable[str] = ("USD", "GBP")) -> RatesResult:
    """
    Fetch latest FX rates from Frankfurter and cache for 6 hours.
    Frankfurter uses ECB reference rates (typically updated on weekdays). :contentReference[oaicite:2]{index=2}
    """
    symbols = tuple(symbols)
    cache_key = f"fx:latest:{base}:{','.join(symbols)}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    params = {"from": base, "to": ",".join(symbols)}
    r = requests.get(FRANKFURTER_LATEST, params=params, timeout=8)
    r.raise_for_status()
    data = r.json()

    rates = {k: Decimal(str(v)) for k, v in data.get("rates", {}).items()}
    result = RatesResult(base=data.get("base", base), date=data.get("date", ""), rates=rates)

    cache.set(cache_key, result, 60 * 60 * 6)  # 6 hours
    return result


def convert(amount: Decimal, rate: Decimal) -> Decimal:
    return (amount * rate).quantize(Decimal("0.01"))
