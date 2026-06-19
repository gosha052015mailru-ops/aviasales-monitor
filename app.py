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

	price_17 = prices.get("17 июля")

	if price_17 is not None and price_17 < 23000:
		send_email(
			subject="Билет на 17 июля дешевле 23 000 ₽",
			body=f"""
	Обнаружена цена ниже 23 000 ₽.

	Дата:
	17 июля

	Цена:
	{price_17:,} ₽

	Ссылка:
	{result.final_url}
	""".replace(",", " ")
		)

		logging.info(
			"Отправлено уведомление: 17 июля цена %s ₽",
			price_17,
		)

	return 0

if __name__ == "__main__":
	try:
		raise SystemExit(main())

	except Exception:
		error_text = traceback.format_exc()

		logging.exception("Критическая ошибка приложения")

		try:
			send_email(
				subject="Ошибка мониторинга билетов",
				body=f"""
Во время выполнения app.py произошла ошибка.

Traceback:

{error_text}
"""
			)
		except Exception:
			logging.exception("Не удалось отправить письмо об ошибке")

		raise
