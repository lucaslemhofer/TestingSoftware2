import re
from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class LoginPage(BasePage):
    # DOM observado el 06/10/2026; ninguna credencial se guarda en codigo.
    EMAIL = (By.ID, 'email')
    PASSWORD = (By.ID, 'password')
    SUBMIT = (By.CSS_SELECTOR, "form[action='../actions/login_procesar.php'] button[type='submit']")
    LIST = (By.CSS_SELECTOR, "nav a[href='expedientes.php']")

    def open(self, url):
        self.driver.get(url)
        self.visible(self.EMAIL)
        self.visible(self.PASSWORD)
        return self

    def fill(self, email, password):
        self.set_text(self.EMAIL, email)
        self.set_text(self.PASSWORD, password)

    def submit(self):
        self.click(self.SUBMIT)

    def wait_authenticated(self):
        self.visible(self.LIST)

    def demo_credentials(self, role):
        body = self.visible(self.BODY).text
        user = re.search(re.escape(role) + r'\s+([^\s]+@[^\s]+)', body)
        password = re.search(r'Todas utilizan la contrase\S+\s+(\S+)', body)
        assert user and password, 'No se encontraron las credenciales publicadas para el rol solicitado'
        return user.group(1), password.group(1)
