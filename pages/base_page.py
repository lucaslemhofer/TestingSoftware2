from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException


class BasePage:
    BODY = (By.TAG_NAME, 'body')
    USER_NAME = (By.CSS_SELECTOR, 'header button strong')

    def __init__(self, driver, timeout=20):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def set_text(self, locator, value):
        value = str(value)
        actual = ''
        # Usar las acciones nativas de Selenium y verificar también después
        # del blur: algunos controles actualizan su valor al perder el foco.
        for _ in range(2):
            field = self.visible(locator)
            field.click()
            field.clear()
            if value:
                field.send_keys(value)
            try:
                check = WebDriverWait(self.driver, min(self.timeout, 3))
                check.until(lambda d: (d.find_element(*locator).get_attribute('value') or '') == value)
                field = self.visible(locator)
                field.send_keys(Keys.TAB)
                check.until(lambda d: (d.find_element(*locator).get_attribute('value') or '') == value)
                return
            except TimeoutException:
                actual = self.driver.find_element(*locator).get_attribute('value') or ''

        actual = self.visible(locator).get_attribute('value') or ''
        if actual != value:
            field = self.visible(locator)
            ident = field.get_attribute('id') or field.get_attribute('name') or str(locator)
            raise AssertionError(
                f"No se pudo ingresar el valor esperado en el campo {ident!r}: "
                f"se esperaba {value!r} y quedó {actual!r}"
            )

    def navigate_click(self, locator):
        # SIGEX puede reemplazar el menú durante una redirección. Volver a
        # localizar el control evita operar sobre una referencia obsoleta.
        for attempt in range(3):
            try:
                element = self.visible(locator)
                href = element.get_attribute('href') if element.tag_name == 'a' else None
                if href:
                    # Reutilizar la URL del enlace también reinicia filtros activos.
                    self.driver.get(href)
                else:
                    # click() espera la navegación normal del formulario. No usar
                    # staleness_of(body): Chrome puede invalidar ese nodo demasiado pronto.
                    element.click()
                self.wait.until(lambda driver: driver.execute_script(
                    'return document.readyState') == 'complete')
                self.visible(self.BODY)
                return
            except StaleElementReferenceException:
                if attempt == 2:
                    raise

    def user_name(self):
        return self.visible(self.USER_NAME).text.strip()

    def validity(self, locator):
        return self.driver.execute_script(
            'return {valid:arguments[0].validity.valid, missing:arguments[0].validity.valueMissing, mismatch:arguments[0].validity.typeMismatch, patternMismatch:arguments[0].validity.patternMismatch}',
            self.visible(locator))
