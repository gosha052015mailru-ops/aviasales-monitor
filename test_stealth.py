from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time

def test_stealth():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="ru-RU",
            timezone_id="Europe/Moscow"
        )
        page = context.new_page()
        
        # Применяем Stealth по-новому
        Stealth().apply_stealth_sync(page)
        
        print("Открываем страницу в Stealth-режиме...")
        page.goto("https://www.aeroflot.ru/sb/subsidized/app/ru-ru#/search", wait_until="domcontentloaded")
        
        print("Ждем 10 секунд для прохождения проверок...")
        time.sleep(10)
        
        html = page.content()
        html_lower = html.lower()
        title = page.title()
        
        print(f"Заголовок страницы: {title}")
        
        if "аэрофлот" in html_lower or "субсидированн" in html_lower or "search-form" in html_lower:
            print("✅ STEALTH УСПЕШЕН! Мы получили доступ к сайту.")
            # Сохраняем чтобы посмотреть, что отдали
            with open("success.html", "w") as f:
                f.write(html)
        else:
            print(f"🛑 Stealth НЕ пробил защиту. Длина HTML: {len(html)}")
            print("--- Тело страницы (первые 500 символов) ---")
            print(html[:500])
            
        browser.close()

if __name__ == "__main__":
    test_stealth()
