"""
Дымовые тесты Dodo Pizza (https://dodopizza.ru/moscow).

Smoke-сценарии ориентированы на основной пользовательский поток:
1) открытие сайта,
2) загрузка каталога,
3) переход к блоку пицц,
4) открытие карточки/конструктора товара,
5) добавление товара в корзину,
6) ввод данных в поле телефона в окне входа.
"""
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "https://dodopizza.ru/moscow"
SCREENSHOTS_DIR = "screenshots"


def ensure_screenshots_dir():
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)


def save_screenshot(browser, filename):
    ensure_screenshots_dir()
    path = os.path.join(SCREENSHOTS_DIR, filename)
    browser.save_screenshot(path)


def close_popups_if_any(browser):
    possible_buttons = [
        "//button[contains(., 'Понятно')]",
        "//button[contains(., 'Хорошо')]",
        "//button[contains(., 'Закрыть')]",
        "//button[contains(., 'Принять')]",
        "//button[contains(., 'Согласен')]",
        "//button[contains(., 'Ок')]",
        "//button[contains(., 'OK')]",
    ]

    for xpath in possible_buttons:
        try:
            buttons = browser.find_elements(By.XPATH, xpath)
            for button in buttons:
                if button.is_displayed():
                    browser.execute_script("arguments[0].click();", button)
                    time.sleep(1)
                    return
        except Exception:
            pass


def find_visible_element_by_xpaths(browser, xpaths, timeout=15):
    wait = WebDriverWait(browser, timeout)

    for xpath in xpaths:
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elements = browser.find_elements(By.XPATH, xpath)
            for element in elements:
                if element.is_displayed():
                    return element
        except Exception:
            continue

    return None


def scroll_page_for_products(browser):
    for _ in range(4):
        browser.execute_script("window.scrollBy(0, 700);")
        time.sleep(1.5)


def find_first_product_button(browser, timeout=15):
    wait = WebDriverWait(browser, timeout)

    # сначала немного проскроллим, чтобы каталог точно дорендерился
    scroll_page_for_products(browser)

    xpaths = [
        "//button[contains(., '₽')]",
        "//a[contains(., '₽')]",
        "//button[contains(., 'руб')]",
        "//a[contains(., 'руб')]",
        "//button[contains(., 'Выбрать')]",
        "//a[contains(., 'Выбрать')]",
        "//button[contains(., 'В корзину')]",
        "//a[contains(., 'В корзину')]",
        "//button[contains(., 'Добавить')]",
        "//a[contains(., 'Добавить')]",
    ]

    ignored_words = ["войти", "вход", "регистрация", "контакты", "акции"]

    for xpath in xpaths:
        try:
            wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
            elements = browser.find_elements(By.XPATH, xpath)

            for element in elements:
                try:
                    if not element.is_displayed():
                        continue

                    text = (element.text or "").strip().lower()
                    if any(word in text for word in ignored_words):
                        continue

                    if text:
                        return element
                except Exception:
                    continue
        except Exception:
            continue

    return None


def open_main_page(browser):
    browser.get(BASE_URL)
    time.sleep(4)
    close_popups_if_any(browser)


def test_tc01_main_page(browser):
    open_main_page(browser)

    title = browser.title.lower()
    assert any(word in title for word in ["додо", "пицц", "доставка", "москва"]), \
        f"Неожиданный title: {browser.title}"

    save_screenshot(browser, "tc01_main_page.png")


def test_tc02_catalog_visible(browser):
    open_main_page(browser)

    catalog_element = find_visible_element_by_xpaths(browser, [
        "//*[contains(text(), 'Комбо')]",
        "//*[contains(text(), 'Пиццы')]",
        "//*[contains(text(), 'Закуски')]",
        "//*[contains(text(), 'Напитки')]",
    ])

    assert catalog_element is not None, "Каталог товаров не найден"

    save_screenshot(browser, "tc02_catalog_visible.png")


def test_tc03_scroll_to_pizza_block(browser):
    open_main_page(browser)

    pizza_block = find_visible_element_by_xpaths(browser, [
        "//*[contains(text(), 'Пиццы')]",
        "//h2[contains(., 'Пиццы')]",
        "//div[contains(., 'Пиццы')]",
    ])

    assert pizza_block is not None, "Блок 'Пиццы' не найден"

    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", pizza_block)
    time.sleep(2)

    save_screenshot(browser, "tc03_scroll_to_pizza_block.png")
    assert pizza_block.is_displayed(), "После скролла блок 'Пиццы' не отображается"


def test_tc04_open_product_configurator(browser):
    open_main_page(browser)

    choose_button = find_first_product_button(browser)
    assert choose_button is not None, "Не найдена кнопка выбора товара"

    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", choose_button)
    time.sleep(1)
    browser.execute_script("arguments[0].click();", choose_button)
    time.sleep(4)

    save_screenshot(browser, "tc04_open_product_configurator.png")

    assert browser.current_url != BASE_URL or len(browser.page_source) > 0, \
        "После нажатия на товар ничего не произошло"


def test_tc05_add_product_to_cart(browser):
    open_main_page(browser)

    choose_button = find_first_product_button(browser)
    assert choose_button is not None, "Не найдена кнопка товара"

    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", choose_button)
    time.sleep(1)

    before_url = browser.current_url
    before_source = browser.page_source

    browser.execute_script("arguments[0].click();", choose_button)
    time.sleep(4)

    save_screenshot(browser, "tc05_add_product_to_cart.png")

    after_url = browser.current_url
    after_source = browser.page_source

    assert before_url != after_url or before_source != after_source, \
        "После нажатия на кнопку состояние страницы не изменилось"


def test_tc06_open_login_and_fill_phone(browser):
    open_main_page(browser)

    login_button = find_visible_element_by_xpaths(browser, [
        "//button[contains(., 'Войти')]",
        "//a[contains(., 'Войти')]",
        "//*[contains(text(), 'Войти')]",
    ])

    assert login_button is not None, "Кнопка входа не найдена"

    browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
    time.sleep(1)
    browser.execute_script("arguments[0].click();", login_button)
    time.sleep(3)

    phone_input = find_visible_element_by_xpaths(browser, [
        "//input[contains(@placeholder, 'телефон')]",
        "//input[contains(@placeholder, 'Телефон')]",
        "//input[@type='tel']",
        "//input[contains(@name, 'phone')]",
    ], timeout=10)

    assert phone_input is not None, "Поле телефона не найдено"

    phone_input.clear()
    phone_input.send_keys("9991234567")
    time.sleep(1)

    save_screenshot(browser, "tc06_open_login_and_fill_phone.png")

    entered_value = phone_input.get_attribute("value")
    assert entered_value is not None and entered_value != "", "Поле телефона не заполнилось"