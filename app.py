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
    f = send_email(
		"Тест с сервера",
		"Если вы получили это письмо, SMTP работает."
	)
    prices = extract_prices(result.html_content)
    print("\nЦены:")
    for day in [
		"15 июля",
		"16 июля",
		"17 июля",
		"18 июля",
		"19 июля",
		"20 июля",
	]:
        print(f"{day}: {prices.get(day)}")

    logging.info("Статус: %s", result.status)
    logging.info("Сообщение: %s", result.message)
    logging.info("Итоговый URL: %s", result.final_url)
    
	

    # Простейшая проверка наличия числа 21000 на странице (например, цены)
    if "21000" in result.html_content or "21 000" in result.html_content:
        logging.info("ЦЕНА ПРОВЕРКИ: На странице найдено число 21000 (или 21 000)!")
    else:
        logging.info("ЦЕНА ПРОВЕРКИ: Числа 21000 на странице не найдено.")

if __name__ == "__main__":
    raise SystemExit(main())
