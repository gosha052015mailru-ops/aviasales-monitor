from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
	target_url: str
	subsidy_program: str
	departure_city: str
	arrival_city: str
	departure_code: str
	arrival_code: str
	departure_date: date
	passenger_category: str
	headless: bool
	browser_timeout_ms: int


def _to_bool(value: str, default: bool = False) -> bool:
	if not value:
		return default
	return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> AppConfig:
	load_dotenv()

	target_url = os.getenv(
		"TARGET_URL",
		"https://www.aeroflot.ru/sb/subsidized/app/ru-ru#/search",
	)
	subsidy_program = os.getenv("SUBSIDY_PROGRAM", "Молодежь и пенсионеры")
	departure_city = os.getenv("DEPARTURE_CITY", "Москва")
	arrival_city = os.getenv("ARRIVAL_CITY", "Якутск")
	departure_code = os.getenv("DEPARTURE_CODE", "MOW")
	arrival_code = os.getenv("ARRIVAL_CODE", "YKS")
	date_raw = os.getenv("DEPARTURE_DATE", "2026-07-17")
	departure_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
	passenger_category = os.getenv("PASSENGER_CATEGORY", "Молодежь")
	headless = _to_bool(os.getenv("HEADLESS", "false"), default=False)
	browser_timeout_ms = int(os.getenv("BROWSER_TIMEOUT_MS", "30000"))

	return AppConfig(
		target_url=target_url,
		subsidy_program=subsidy_program,
		departure_city=departure_city,
		arrival_city=arrival_city,
		departure_code=departure_code,
		arrival_code=arrival_code,
		departure_date=departure_date,
		passenger_category=passenger_category,
		headless=headless,
		browser_timeout_ms=browser_timeout_ms,
	)
