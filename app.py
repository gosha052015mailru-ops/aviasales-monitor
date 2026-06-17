from __future__ import annotations

import logging
from pathlib import Path

from checker import fill_subsidy_form, parse_program_options_from_html
from config import load_config
from notifier import send_email
from checker import extract_prices

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> int:
	setup_logging()
	cfg = load_config()

	html_file = Path(__file__).with_name("subsidi.html")
	if html_file.exists():
		options = parse_program_options_from_html(html_file)
		logging.info(
			"Найдено программ субсидирования в локальном HTML: %s",
			", ".join(opt.text for opt in options),
		)

	result = fill_subsidy_form(cfg)

	prices = extract_prices(result.html_content)
	if not prices:
		send_email(
			subject="Ошибка парсинга Аэрофлот",
			body=f"""Не удалось получить цены со страницы."""
		)
		return 0

	target_days = [
		"15 июля",
		"16 июля",
		"17 июля",
		"18 июля",
		"19 июля",
	]

	for day in target_days:
		price = prices.get(day)

		if price is None:
			print(f"{day}: нет рейса")
			continue

		print(f"{day}: {price:,} ₽".replace(",", " "))

		if day in target_days and price <= 15000:
			send_email(
				subject="Найден субсидированный билет",
				body=f"""Найден субсидированный билет на {day} по цене {price} ₽!"""
			)
			print(f"Отправлено уведомление на почту о билете за {price} ₽ на {day}.")
	logging.info("Статус: %s", result.status)
	logging.info("Сообщение: %s", result.message)

	return 0

if __name__ == "__main__":
    raise SystemExit(main())
