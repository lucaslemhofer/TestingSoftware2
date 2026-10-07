from selenium.webdriver.common.by import By
from datetime import date
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from pages.base_page import BasePage


class ExpedientesPage(BasePage):
    NEW = (By.CSS_SELECTOR, "nav a[href='mesa_entrada.php']")
    LIST = (By.CSS_SELECTOR, "nav a[href='expedientes.php']")
    FORM = (By.CSS_SELECTOR, "form[action='../actions/expediente_guardar.php']")
    NUMBER = (By.ID, 'numero')
    FIELDS = {name: (By.ID, ident) for name, ident in {
        'numero': 'numero', 'caratula': 'caratula', 'actor': 'actor',
        'demandado': 'demandado', 'juzgado': 'juzgado', 'fecha': 'ingreso',
        'observaciones': 'observaciones', 'designacion': 'designacion'}.items()}
    SAVE = (By.CSS_SELECTOR, "form[action='../actions/expediente_guardar.php'] button:not([type='button']):not([type='reset'])")
    RESET = (By.CSS_SELECTOR, "form[action='../actions/expediente_guardar.php'] button[type='reset']")
    INITIAL_OWNER = (By.NAME, 'responsable_actual_id')
    REQUIRED_SELECTS = (
        (By.ID, 'tipo-expediente'),
        (By.ID, 'dependencia'),
        (By.ID, 'secretaria'),
        (By.ID, 'fuero'),
        (By.ID, 'materia'),
        (By.ID, 'categoria'),
        (By.ID, 'tipo'),
        (By.ID, 'elevacion'),
    )
    SEARCH = {name: (By.NAME, name) for name in ('numero', 'parte', 'caratula', 'tipo_causa_id', 'materia_id', 'estado', 'tipo_elevacion')}
    APPLY = (By.XPATH, "//button[normalize-space()='Aplicar filtros']")
    ROWS = (By.CSS_SELECTOR, 'table tbody tr')
    ROW_NUMBER = (By.CSS_SELECTOR, 'td:first-child .mono')
    DETAIL = (By.CSS_SELECTOR, "a[href^='expediente_detalle.php?id=']")
    HEADING = (By.TAG_NAME, 'h1')
    HISTORY = (By.CSS_SELECTOR, 'aside ol.timeline')
    HISTORY_ITEMS = (By.CSS_SELECTOR, 'aside ol.timeline li')
    DESTINATION = (By.NAME, 'usuario_destino_id')
    STATE = (By.NAME, 'estado_nuevo')
    COMMENT = (By.NAME, 'comentario')
    TRANSFER = (By.CSS_SELECTOR, "form[action='../actions/pase_guardar.php'] button:not([type='button']):not([type='reset'])")

    def new(self):
        self.navigate_click(self.NEW)
        self.visible(self.NUMBER)

    def fill(self, number, owner=None):
        # No usar "Completar para prueba": carga datos fijos del sitio y puede
        # sobrescribir los valores sinteticos mientras se preparan los CP.
        # La prueba completa de forma explicita todos los datos que necesita.
        # Primero resolver las listas dependientes, antes de escribir textos.
        for locator in self.REQUIRED_SELECTS:
            self.select_first_valid(locator)
        self.select_owner(owner or self.user_name())

        # Completar textos después de las listas, para que la preparación no
        # los vuelva a borrar antes de comprobar el caso.
        self.set_text(self.FIELDS['actor'], 'Actor sintetico ' + number)
        self.set_text(self.FIELDS['demandado'], 'Demandado sintetico ' + number)
        self.set_text(self.FIELDS['caratula'], 'Caratula sintetica ' + number)
        self.set_text(self.FIELDS['designacion'], 'Expediente de prueba automatizada')
        self.set_text(self.FIELDS['juzgado'], 'Juzgado de prueba N.º 1')
        fecha = self.visible(self.FIELDS['fecha'])
        if not fecha.get_attribute('value'):
            fecha.send_keys(date.today().isoformat())
        # Algunas acciones de la página pueden normalizar campos en cascada;
        # escribir el identificador al final y comprobarlo antes de seguir.
        self.set_text(self.NUMBER, number)
        actual_numero = self.visible(self.NUMBER).get_attribute('value')
        if actual_numero != number:
            raise AssertionError(
                f"SIGEX no conservó el número de prueba (esperado {number!r}, "
                f"obtenido {actual_numero!r})"
            )

        expected_text = {
            'actor': 'Actor sintetico ' + number,
            'demandado': 'Demandado sintetico ' + number,
            'caratula': 'Caratula sintetica ' + number,
            'designacion': 'Expediente de prueba automatizada',
            'juzgado': 'Juzgado de prueba N.º 1',
        }
        for name, expected in expected_text.items():
            actual = self.visible(self.FIELDS[name]).get_attribute('value')
            if actual != expected:
                raise AssertionError(
                    f"La preparación no conservó {name}: se esperaba el valor de prueba y quedó vacío o distinto"
                )

        invalidos = self.invalid_fields()
        if invalidos:
            detalle = [
                f"{field.get_attribute('name') or field.get_attribute('id')}: "
                f"{field.get_attribute('validationMessage')}"
                for field in invalidos
            ]
            raise AssertionError(
                'La preparación del caso dejó campos requeridos inválidos: '
                + '; '.join(detalle)
            )

    def select_first_valid(self, locator):
        def ready(driver):
            element = driver.find_element(*locator)
            if not element.is_enabled():
                return False
            options = [
                option for option in Select(element).options
                if option.get_attribute('value') and option.is_enabled()
            ]
            return options or False

        options = self.wait.until(ready)
        select = Select(self.visible(locator))
        if select.first_selected_option.get_attribute('value'):
            return
        select.select_by_value(options[0].get_attribute('value'))

    def select_owner(self, name):
        select = Select(self.visible(self.INITIAL_OWNER))
        matches = [o for o in select.options if o.text.split(' · ')[0].strip() == name]
        assert len(matches) == 1, 'Responsable de prueba ausente o ambiguo'
        select.select_by_value(matches[0].get_attribute('value'))

    def invalid_fields(self):
        return self.visible(self.FORM).find_elements(By.CSS_SELECTOR, ':invalid')

    def save(self):
        self.click(self.SAVE)

    def reset(self):
        self.click(self.RESET)

    def search(self, number='', **filters):
        # Tras guardar, SIGEX a veces conserva brevemente la vista de detalle.
        # Confirmar que cargó el formulario de filtros y reintentar la navegación
        # una vez evita continuar con selectores de la página equivocada.
        for attempt in range(2):
            self.navigate_click(self.LIST)
            try:
                WebDriverWait(self.driver, min(self.timeout, 5)).until(
                    EC.visibility_of_element_located(self.SEARCH['numero'])
                )
                break
            except TimeoutException:
                if attempt == 1:
                    raise AssertionError(
                        'SIGEX no cargó el filtro de número en la lista de expedientes'
                    )
        self.set_text(self.SEARCH['numero'], number)
        for name, value in filters.items():
            if name in ('numero', 'parte', 'caratula'):
                self.set_text(self.SEARCH[name], value)
            else:
                Select(self.visible(self.SEARCH[name])).select_by_visible_text(value)
        field = self.visible(self.SEARCH['numero'])
        assert field.get_attribute('value') == number, 'El numero del filtro no conserva el texto ingresado'
        old_url = self.driver.current_url
        old_numbers = tuple(self.numbers())
        self.click(self.APPLY)

        def results_updated(driver):
            if driver.current_url != old_url:
                return True
            try:
                body_text = driver.find_element(*self.BODY).text
                current_numbers = tuple(self.numbers())
                return (
                    current_numbers != old_numbers
                    or 'No se encontraron expedientes' in body_text
                )
            except StaleElementReferenceException:
                return False

        # El sitio puede recargar la página o actualizar la tabla en el mismo
        # documento; comparar resultados evita depender de un body obsoleto.
        self.wait.until(results_updated)
        self.visible(self.SEARCH['numero'])

    def rows(self):
        return [r for r in self.driver.find_elements(*self.ROWS) if r.find_elements(*self.ROW_NUMBER)]

    def exact_rows(self, number):
        # Comparacion de texto sin interpolar datos en XPath.
        return [r for r in self.rows() if r.find_element(*self.ROW_NUMBER).text.strip() == number]

    def numbers(self):
        return [r.find_element(*self.ROW_NUMBER).text.strip() for r in self.rows()]

    def create(self, number, owner=None):
        self.new()
        self.fill(number, owner)
        self.save()
        self.search(number)
        assert len(self.exact_rows(number)) == 1, 'El alta no produjo exactamente un registro'

    def detail(self, number):
        self.search(number)
        rows = self.exact_rows(number)
        assert len(rows) == 1, 'Se esperaba un expediente unico'
        old_url = self.driver.current_url
        rows[0].find_element(*self.DETAIL).click()
        self.wait.until(lambda driver: driver.current_url != old_url)
        assert self.visible(self.HEADING).text == number

    def field_value(self, label):
        # Etiquetas fijas de la interfaz, no datos externos.
        return self.visible((By.XPATH, "//dt[normalize-space()='" + label + "']/following-sibling::dd[1]")).text.strip()

    def list_state(self, number):
        self.search(number)
        rows = self.exact_rows(number)
        assert len(rows) == 1
        return rows[0].find_elements(By.TAG_NAME, 'td')[3].text.strip()

    def history(self):
        return self.visible(self.HISTORY).text

    def movement(self, comment):
        items = [e for e in self.driver.find_elements(*self.HISTORY_ITEMS) if comment in e.text]
        assert len(items) == 1, 'El movimiento no aparece exactamente una vez en el historial'
        return items[0].text

    def transfer(self, comment):
        select = Select(self.visible(self.DESTINATION))
        options = [o for o in select.options if 'Secretario Relator' in o.text]
        assert len(options) == 1, 'Destino de prueba ausente o ambiguo'
        target = options[0].text.split(' · ')[0]
        select.select_by_value(options[0].get_attribute('value'))
        Select(self.visible(self.STATE)).select_by_visible_text('En trámite')
        self.set_text(self.COMMENT, comment)
        self.navigate_click(self.TRANSFER)
        self.driver.refresh()
        self.visible(self.HEADING)
        assert comment in self.history(), 'El pase no quedo registrado'
        assert self.field_value('Responsable actual') == target
        return target

    def transfer_without_destination(self):
        Select(self.visible(self.DESTINATION)).select_by_value('')
        self.click(self.TRANSFER)
