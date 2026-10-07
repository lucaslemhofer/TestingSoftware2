import base64
import os
import re
import warnings
from datetime import datetime
from pathlib import Path

import pytest
import pytest_html
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from pages.login_page import LoginPage
from pages.expedientes_page import ExpedientesPage

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env', override=False)
SECRETS = set()


def pytest_addoption(parser):
    parser.addoption('--read-only', action='store_true', help='Omitir casos que pueden crear o modificar datos')


def pytest_collection_modifyitems(config, items):
    for item in items:
        if config.getoption('--read-only') and item.get_closest_marker('writes'):
            item.add_marker(pytest.mark.skip(reason='Modo --read-only: requiere datos sinteticos nuevos'))


@pytest.fixture
def driver(request):
    options = Options()
    if os.getenv('HEADLESS', 'true').lower() == 'true':
        options.add_argument('--headless=new')
    options.add_argument('--window-size=1440,1000')
    options.add_argument('--disable-notifications')
    # Evita el aviso de contraseñas filtradas en el perfil temporal de Selenium.
    # No modifica la configuración del Chrome habitual del usuario.
    options.add_experimental_option('prefs', {
        'profile.password_manager_leak_detection': False,
    })
    path = os.getenv('CHROMEDRIVER')
    browser = webdriver.Chrome(service=Service(path) if path else Service(), options=options)
    request.node._browser = browser
    try:
        browser.set_page_load_timeout(40)
        yield browser
    finally:
        browser.quit()
        request.node._browser = None


@pytest.fixture
def login(driver):
    return LoginPage(driver, int(os.getenv('TIMEOUT', '20'))).open(
        os.getenv('SIGEX_LOGIN_URL', 'https://sigex.unaux.com/public/login.php'))


@pytest.fixture
def authenticate(request):
    # Comprobar credenciales antes de iniciar Chrome; faltantes -> SKIP, login fallido -> ERROR.
    def sign_in(role='Mesa de Entrada'):
        prefix = 'SIGEX_RELATOR' if role == 'Secretario Relator' else 'SIGEX'
        user, password = os.getenv(prefix + '_USER'), os.getenv(prefix + '_PASSWORD')
        demo = os.getenv('SIGEX_USE_DEMO', 'false').lower() == 'true'
        if not demo and not (user and password):
            pytest.skip('Faltan ' + prefix + '_USER y ' + prefix + '_PASSWORD en .env')
        browser = request.getfixturevalue('driver')
        browser.delete_all_cookies()
        page = LoginPage(browser, int(os.getenv('TIMEOUT', '20'))).open(
            os.getenv('SIGEX_LOGIN_URL', 'https://sigex.unaux.com/public/login.php'))
        if demo:
            user, password = page.demo_credentials(role)
        SECRETS.update((user, password))
        page.fill(user, password)
        page.submit()
        page.wait_authenticated()
        return ExpedientesPage(browser, page.timeout)
    return sign_in


@pytest.fixture
def expedientes(authenticate):
    return authenticate()


@pytest.fixture
def numero():
    from data.test_data import nuevo_expediente
    return nuevo_expediente()['numero']


@pytest.fixture
def creado(expedientes, numero):
    expedientes.create(numero)
    expedientes.detail(numero)
    return expedientes, numero


@pytest.fixture
def movido(creado):
    page, number = creado
    actor = page.user_name()
    comment = 'Movimiento sintetico ' + number
    destination = page.transfer(comment)
    return page, number, comment, actor, destination


@pytest.fixture
def borrador(authenticate, numero):
    from pages.documentos_page import DocumentosPage
    # Verificar la segunda cuenta antes de crear datos.
    relator = authenticate('Secretario Relator')
    owner = relator.user_name()
    page = authenticate()
    page.create(numero, owner=owner)
    page = authenticate('Secretario Relator')
    page.detail(numero)
    docs = DocumentosPage(page.driver, page.timeout)
    title, content = 'Sentencia ' + numero, 'Contenido original ' + numero
    docs.create(title, content)
    docs.open_document(title)
    return docs, title, content, numero


def redact(text):
    secrets = SECRETS | {v for k, v in os.environ.items() if k.startswith('SIGEX') and ('PASSWORD' in k or k.endswith('_USER')) and v}
    for value in sorted(secrets, key=len, reverse=True):
        text = text.replace(value, '[REDACTADO]')
    return text


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    report.sections = [(name, redact(content)) for name, content in report.sections]
    if report.failed and report.longrepr:
        report.longrepr = redact(str(report.longrepr))
    # Guardar captura una sola vez y únicamente cuando falla la ejecución del test.
    if report.when != 'call' or not report.failed:
        return
    browser = getattr(item, '_browser', None)
    if browser is None:
        return
    masked = False
    try:
        # Ocultamiento temporal: el DOM se restaura incluso si falla la captura.
        browser.execute_script("""
            window.__sigexMask = [];
            document.querySelectorAll('input,textarea').forEach(e => {
                window.__sigexMask.push([e, 'style', e.getAttribute('style')]);
                e.style.visibility = 'hidden';
            });
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const n = walker.currentNode;
                if (/@|password|contrase/i.test(n.textContent)) {
                    window.__sigexMask.push([n, 'text', n.textContent]);
                    n.textContent = '[REDACTADO]';
                }
            }
        """)
        masked = True
        folder = ROOT / 'screenshots'
        folder.mkdir(exist_ok=True)
        name = re.sub(r'[^a-zA-Z0-9_-]', '_', item.nodeid)
        path = folder / f'{name}_{report.when}_{datetime.now():%Y%m%d_%H%M%S_%f}.png'
        image = browser.get_screenshot_as_base64()
        path.write_bytes(base64.b64decode(image))
        report.extras = getattr(report, 'extras', []) + [pytest_html.extras.png(image, name='Captura de fallo')]
    except Exception as exc:
        warnings.warn(f'No se pudo generar captura ({type(exc).__name__})', RuntimeWarning)
    finally:
        if masked:
            try:
                browser.execute_script("""
                    for (const [e, kind, value] of window.__sigexMask || []) {
                        if (kind === 'text') e.textContent = value;
                        else if (value === null) e.removeAttribute('style');
                        else e.setAttribute('style', value);
                    }
                    delete window.__sigexMask;
                """)
            except Exception:
                pass
