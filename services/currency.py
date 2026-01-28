from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, Union

import requests
from django.core.cache import cache


FRANKFURTER_LATEST = "https://api.frankfurter.app/latest"


@dataclass(frozen=True)
class RatesResult:
    base: str
    date: str
    rates: Dict[str, Decimal]


def get_latest_rates(
    base: str = "EUR",
    symbols: Iterable[str] = ("USD", "GBP"),
) -> RatesResult:
    """
    Fetch latest FX rates from Frankfurter and cache for 6 hours.
    Frankfurter uses ECB reference rates 
    """
    symbols = tuple(symbols)
    cache_key = f"fx:latest:{base}:{','.join(symbols)}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    params = {"from": base, "to": ",".join(symbols)}
    response = requests.get(FRANKFURTER_LATEST, params=params, timeout=8)
    response.raise_for_status()
    data = response.json()

    rates = {k: Decimal(str(v)) for k, v in data.get("rates", {}).items()}

    result = RatesResult(
        base=data.get("base", base),
        date=data.get("date", ""),
        rates=rates,
    )

    cache.set(cache_key, result, 60 * 60 * 6)  # cache for 6 hours
    return result


Number = Union[int, float, Decimal]


def convert(amount: Number, rate: Number) -> Decimal:
    """
    Convert an amount using a rate.
    Accepts int/float/Decimal and returns a quantized Decimal (2dp).
    """
    amount_d = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    rate_d = rate if isinstance(rate, Decimal) else Decimal(str(rate))

    return (amount_d * rate_d).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
