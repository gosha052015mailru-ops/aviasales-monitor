from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
from playwright_stealth import Stealth

from config import AppConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedProgramOption:
    text: str


@dataclass(frozen=True)
class FillResult:
    status: str
    final_url: str
    message: str
    html_content: str = ""


def parse_program_options_from_html(file_path: str | Path) -> list[ParsedProgramOption]:
    html = Path(file_path).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    items: list[ParsedProgramOption] = []
    for btn in soup.select(".dropdown__items-item button"):
        txt = btn.get_text(" ", strip=True)
        if txt:
            items.append(ParsedProgramOption(text=txt))
    return items


def build_prefilled_search_url(cfg: AppConfig) -> str:
    route_date = cfg.departure_date.strftime("%Y%m%d")
    params = {
        "program_id": "40",
        "large_family": "0",
        "invalid_1": "0",
        "invalid_2_3": "0",
        "dfo_resident": "0",
        "kgd_resident": "0",
        "youth": "1",
        "seniorw": "0",
        "seniorm": "0",
        "teen_invalid": "0",
        "attendant": "0",
        "attendant_child": "0",
        "kgd_student": "0",
        "child": "0",
        "dfo_child": "0",
        "kgd_child": "0",
        "large_child": "0",
        "child_invalid": "0",
        "dfo_infant": "0",
        "infant": "0",
        "kgd_infant": "0",
        "infant_invalid": "0",
        "routes": f"{cfg.departure_code}.{route_date}.{cfg.arrival_code}",
    }
    return (
        "https://www.aeroflot.ru/sb/subsidized/app/ru-ru#/search?"
        f"{urlencode(params)}"
    )


def _is_anti_bot_page(html: str) -> bool:
    markers = [
        "CODE:",
        "Ваш ID запроса к ресурсу",
        "Если считаете, что произошла ошибка",
    ]
    lowered = html.lower()
    return any(m.lower() in lowered for m in markers)


def _click_button_by_text(page: Page, text: str, timeout_ms: int) -> None:
    page.get_by_role("button", name=text).first.click(timeout=timeout_ms)


def _fill_input_near_label(page: Page, label_text: str, value: str, timeout_ms: int) -> None:
    candidate = page.locator(".input").filter(has=page.get_by_text(label_text, exact=True)).first
    input_box = candidate.locator("input").first
    input_box.click(timeout=timeout_ms)
    input_box.fill(value, timeout=timeout_ms)
    input_box.press("Enter", timeout=timeout_ms)


def _fill_departure_date(page: Page, departure_date: date, timeout_ms: int) -> None:
    formatted = departure_date.strftime("%d.%m.%Y")
    date_container = page.locator(".input").filter(has=page.get_by_text("Туда", exact=True)).first
    date_input = date_container.locator("input").first
    date_input.click(timeout=timeout_ms)
    date_input.fill(formatted, timeout=timeout_ms)
    date_input.press("Enter", timeout=timeout_ms)


def _fill_passenger_category(page: Page, cfg: AppConfig) -> None:
	timeout_ms = cfg.browser_timeout_ms
	try:
		page.locator("#select_classsearch-form-1").click(timeout=timeout_ms)
	except Exception:
		page.get_by_role("button", name="Кто летит").click(timeout=timeout_ms)

	page.wait_for_timeout(1000)

	page.evaluate('''() => {
		const labels = Array.from(document.querySelectorAll('.row label .text.text--inline'));
		const youthLabel = labels.find(l => l.textContent.includes('Молодежь'));
		if (youthLabel) {
			const row = youthLabel.closest('.row');
			const plusBtn = row.querySelector('.input-counter__plus');
			if (plusBtn) plusBtn.click();
		}
	}''')

	page.wait_for_timeout(1000)
	try:
		page.locator(".js-dropdown-close").click(timeout=timeout_ms)
	except:
		page.keyboard.press("Escape")


def fill_subsidy_form(cfg: AppConfig) -> FillResult:
    fallback_url = build_prefilled_search_url(cfg)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=cfg.headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ]
        )
        context = browser.new_context(
            locale="ru-RU",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            timezone_id="Europe/Moscow",
        )
        page = context.new_page()
        page.set_default_timeout(cfg.browser_timeout_ms)

        Stealth().apply_stealth_sync(page)

        try:
            page.goto(cfg.target_url, wait_until="domcontentloaded")
            
            # Проверку на анти-бот делаем с паузой, так как Stealth может немного "прогреваться"
            if _is_anti_bot_page(page.content()):
                page.wait_for_timeout(5000)
                if _is_anti_bot_page(page.content()):
                    return FillResult(
                        status="blocked",
                        final_url=page.url,
                        message="Сайт вернул anti-bot страницу. Нужен запуск с разрешенного IP/сервера.",
                        html_content=page.content()
                    )
            
            _click_button_by_text(page, "Выбрать программу субсидирования", cfg.browser_timeout_ms)
            _click_button_by_text(page, cfg.subsidy_program, cfg.browser_timeout_ms)
            _fill_input_near_label(page, "Город вылета", cfg.departure_city, cfg.browser_timeout_ms)
            _fill_input_near_label(page, "Город прибытия", cfg.arrival_city, cfg.browser_timeout_ms)
            _fill_departure_date(page, cfg.departure_date, cfg.browser_timeout_ms)
            _fill_passenger_category(page, cfg)
            
            # Нажимаем Найти
            _click_button_by_text(page, "Найти", cfg.browser_timeout_ms)
            
            # Ждем загрузки результатов (можно увеличить при необходимости)
            page.wait_for_timeout(10000)
            
            current_url = page.url
            logger.info("Форма заполнена и отправлена через UI. URL: %s", current_url)
            return FillResult(
                status="ok",
                final_url=current_url,
                message="Форма заполнена через UI.",
                html_content=page.content()
            )
        except PlaywrightTimeoutError:
            logger.warning("Таймаут при работе с UI, переключаюсь на fallback URL")
            try:
                page.goto(fallback_url, wait_until="domcontentloaded")
                if _is_anti_bot_page(page.content()):
                    return FillResult(
                        status="blocked",
                        final_url=page.url,
                        message="Сайт заблокировал доступ даже по fallback URL.",
                        html_content=page.content()
                    )
                page.wait_for_timeout(10000)
                return FillResult(
                    status="fallback",
                    final_url=page.url,
                    message="UI таймаут, использован fallback URL.",
                    html_content=page.content()
                )
            except Exception as exc:  # noqa: BLE001
                return FillResult(
                    status="error",
                    final_url=fallback_url,
                    message=f"Не удалось открыть fallback URL: {exc}",
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("UI-сценарий не удался (%s), переключаюсь на fallback URL", exc)
            try:
                page.goto(fallback_url, wait_until="domcontentloaded")
                if _is_anti_bot_page(page.content()):
                    return FillResult(
                        status="blocked",
                        final_url=page.url,
                        message="Сайт заблокировал доступ даже по fallback URL.",
                        html_content=page.content()
                    )
                page.wait_for_timeout(10000)
                return FillResult(
                    status="fallback",
                    final_url=page.url,
                    message="UI сценарий не удался, использован fallback URL.",
                    html_content=page.content()
                )
            except Exception as inner_exc:  # noqa: BLE001
                return FillResult(
                    status="error",
                    final_url=fallback_url,
                    message=f"Не удалось открыть fallback URL: {inner_exc}",
                )
        finally:
            context.close()
            browser.close()
