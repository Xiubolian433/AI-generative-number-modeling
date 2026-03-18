import json
import re
from collections import Counter
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import requests


USER_AGENT = "Mozilla/5.0"
CACHE_TTL_SECONDS = 3600
_CACHE = {}


def _cache_get(cache_key):
    cached = _CACHE.get(cache_key)
    if not cached:
        return None

    cached_at = cached["cached_at"]
    if (datetime.utcnow() - cached_at).total_seconds() > CACHE_TTL_SECONDS:
        return None

    return cached["data"]


def _cache_set(cache_key, data):
    _CACHE[cache_key] = {
        "cached_at": datetime.utcnow(),
        "data": data,
    }
    return data


def _counter_to_dict(counter):
    return {str(key): value for key, value in sorted(counter.items())}


def _build_statistics(draws, special_ball_key, special_field_name):
    white_counter = Counter()
    special_counter = Counter()

    for draw in draws:
        for field in ["Number1", "Number2", "Number3", "Number4", "Number5"]:
            value = draw.get(field)
            if value is not None:
                white_counter[int(value)] += 1

        special_value = draw.get(special_ball_key)
        if special_value is not None:
            special_counter[int(special_value)] += 1

    return {
        "whiteballoccurrences": _counter_to_dict(white_counter),
        special_field_name: _counter_to_dict(special_counter),
    }


def fetch_mega_millions_history():
    cache_key = "mega_history"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = "https://www.megamillions.com/cmspages/utilservice.asmx/GetDrawingPagingData"
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json; charset=utf-8",
    }

    page_number = 1
    page_size = 200
    draws = []
    total_results = None

    while total_results is None or len(draws) < total_results:
        payload = {
            "pageNumber": page_number,
            "pageSize": page_size,
            "startDate": "",
            "endDate": "",
        }
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()

        data = json.loads(response.json()["d"])
        total_results = data["TotalResults"]

        for draw in data["DrawingData"]:
            megaplier = draw.get("Megaplier")
            draws.append(
                {
                    "DrawingDate": draw["PlayDate"],
                    "Number1": draw["N1"],
                    "Number2": draw["N2"],
                    "Number3": draw["N3"],
                    "Number4": draw["N4"],
                    "Number5": draw["N5"],
                    "MegaBall": draw["MBall"],
                    "Megaplier": None if megaplier in (-1, None) else megaplier,
                    "JackPot": None,
                }
            )

        page_number += 1

    return _cache_set(cache_key, draws)


def fetch_mega_millions_statistics():
    cache_key = "mega_stats"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    stats = _build_statistics(fetch_mega_millions_history(), "MegaBall", "megaBalloccurrences")
    return _cache_set(cache_key, stats)


def fetch_powerball_history():
    cache_key = "power_history"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    headers = {"User-Agent": USER_AGENT}
    end_date = date.today()
    first_draw_date = date(2010, 2, 3)
    draws_by_date = {}

    card_pattern = re.compile(r'<a class="card"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)

    while end_date >= first_draw_date:
        response = requests.get(
            "https://www.powerball.com/previous-results",
            params={
                "gc": "powerball",
                "sd": first_draw_date.isoformat(),
                "ed": end_date.isoformat(),
            },
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        html = response.text

        page_draws = []
        for match in card_pattern.finditer(html):
            href = match.group(1)
            snippet = match.group(2)
            query = parse_qs(urlparse(href).query)
            draw_dates = query.get("date")

            if not draw_dates:
                continue

            draw_date = draw_dates[0]
            numbers = re.findall(r'item-powerball">(\d+)<', snippet)
            multiplier_match = re.search(r'<span class="multiplier">([^<]+)</span>', snippet)

            if len(numbers) != 6:
                continue

            page_draws.append(
                {
                    "DrawingDate": draw_date,
                    "Number1": int(numbers[0]),
                    "Number2": int(numbers[1]),
                    "Number3": int(numbers[2]),
                    "Number4": int(numbers[3]),
                    "Number5": int(numbers[4]),
                    "PowerBall": int(numbers[5]),
                    "Jackpot": None,
                    "EstimatedCashValue": None,
                    "PowerPlay": multiplier_match.group(1) if multiplier_match else None,
                }
            )

        if not page_draws:
            break

        for draw in page_draws:
            draws_by_date[draw["DrawingDate"]] = draw

        oldest_page_date = min(datetime.strptime(draw["DrawingDate"], "%Y-%m-%d").date() for draw in page_draws)
        if oldest_page_date <= first_draw_date:
            break

        next_end_date = oldest_page_date - timedelta(days=1)
        if next_end_date >= end_date:
            break
        end_date = next_end_date

    draws = sorted(draws_by_date.values(), key=lambda draw: draw["DrawingDate"], reverse=True)
    return _cache_set(cache_key, draws)


def fetch_powerball_statistics():
    cache_key = "power_stats"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    stats = _build_statistics(fetch_powerball_history(), "PowerBall", "powerballoccurrences")
    return _cache_set(cache_key, stats)
