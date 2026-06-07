from playwright.sync_api import sync_playwright
import time

def test_antibot():
    with sync_playwright() as p:
        # Запускаем браузер
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Открываем страницу...")
        page.goto("https://www.aeroflot.ru/sb/subsidized/app/ru-ru#/search", wait_until="domcontentloaded")
        
        # Даем 10 секунд на прохождение проверки браузера (JavaScript challenge)
        print("Ждем 10 секунд для прохождения антибот проверки...")
        time.sleep(10)
        
        html = page.content().lower()
        title = page.title()
        
        print(f"Заголовок страницы: {title}")
        
        if "выполняется проверка" in html or "code:" in html:
            print("🛑 Playwright НЕ прошел проверку. Сайт всё еще блокирует браузер.")
        elif "аэрофлот" in html or "субсидированн" in html:
            print("✅ Playwright УСПЕШНО прошел проверку! Мы получили доступ к сайту.")
        else:
            print("⚠️ Неизвестный ответ. Длина HTML:", len(html))
            
        browser.close()

if __name__ == "__main__":
    test_antibot()
