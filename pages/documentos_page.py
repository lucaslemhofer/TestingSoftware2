from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from pages.base_page import BasePage


class DocumentosPage(BasePage):
    TITLE = (By.CSS_SELECTOR, '#nuevo-borrador input[name="titulo"]')
    TYPE = (By.CSS_SELECTOR, '#nuevo-borrador select[name="tipo_documento"]')
    CONTENT = (By.CSS_SELECTOR, '#nuevo-borrador textarea[name="contenido"]')
    CREATE = (By.CSS_SELECTOR, '#nuevo-borrador button:not([type="button"]):not([type="reset"])')
    MY_DOCUMENTS = (By.CSS_SELECTOR, "nav a[href='mis_sentencias.php']")
    CARDS = (By.CSS_SELECTOR, 'main article')
    EDIT_LINK = (By.CSS_SELECTOR, "a[href^='?documento_id=']")
    EDIT_CONTENT = (By.NAME, 'contenido')
    CHANGE = (By.NAME, 'descripcion_cambio')
    SAVE = (By.CSS_SELECTOR, "form[action='../actions/documento_guardar.php'] button:not([type='button']):not([type='reset'])")
    VERSIONS = (By.CSS_SELECTOR, '.version-row')
    DIFF_OPEN = (By.CSS_SELECTOR, 'button[data-diff-open]')

    def create(self, title, content, kind='Sentencia'):
        self.set_text(self.TITLE, title)
        Select(self.visible(self.TYPE)).select_by_visible_text(kind)
        self.set_text(self.CONTENT, content)
        self.navigate_click(self.CREATE)

    def create_note(self, title, content):
        self.create(title, content, 'Nota')

    def open_document(self, title):
        self.navigate_click(self.MY_DOCUMENTS)
        cards = [c for c in self.driver.find_elements(*self.CARDS) if title in c.text]
        assert len(cards) == 1, 'El borrador no aparece exactamente una vez en Mis Sentencias'
        cards[0].find_element(*self.EDIT_LINK).click()
        # Esperar el control propio de edición evita el race de staleness(body)
        # observado con Chrome 154 durante las navegaciones.
        self.visible(self.CHANGE)

    def content(self):
        return self.visible(self.EDIT_CONTENT).get_attribute('value')

    def edit(self, content, description):
        self.set_text(self.EDIT_CONTENT, content)
        self.set_text(self.CHANGE, description)
        self.navigate_click(self.SAVE)
        self.visible(self.CHANGE)

    def versions(self):
        return [e.text for e in self.driver.find_elements(*self.VERSIONS)]

    def latest_diff(self):
        rows = self.driver.find_elements(*self.VERSIONS)
        assert rows, 'No hay versiones para comparar'
        rows[0].find_element(*self.DIFF_OPEN).click()

        # El modal de SIGEX no declara role="dialog". Esperar por los rótulos
        # propios de la comparación evita un timeout aunque el modal esté abierto.
        def diff_visible(driver):
            text = driver.find_element(*self.BODY).text
            if 'Agregado' in text and 'Eliminado' in text:
                return text
            return False

        return self.wait.until(diff_visible)
