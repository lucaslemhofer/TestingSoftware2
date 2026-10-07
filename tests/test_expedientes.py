import re

import pytest

pytestmark = pytest.mark.writes


def test_CP01_registrar_expediente(creado):
    page, number = creado
    assert page.visible(page.HEADING).text == number
    page.driver.refresh()
    assert page.field_value('Responsable actual') == page.user_name()
    assert page.list_state(number) == 'Registrado'


@pytest.mark.parametrize('field', [
    pytest.param('numero', id='CP02'),
    pytest.param('caratula', id='CP03'),
])
def test_obligatorio_aislado(expedientes, numero, field):
    expedientes.new()
    expedientes.fill(numero)
    expedientes.visible(expedientes.FIELDS[field]).clear()
    expedientes.save()

    field_elements = expedientes.driver.find_elements(*expedientes.FIELDS[field])
    validity = expedientes.validity(expedientes.FIELDS[field]) if field_elements else {}
    validation_message = (
        field_elements[0].get_attribute('validationMessage')
        if field_elements else ''
    )
    body_text = expedientes.visible(expedientes.BODY).text.lower()
    server_message = re.search(
        r'(falta|obligatori|complet|requerid).{0,80}'
        + ('n[uú]mero' if field == 'numero' else 'car[aá]tula'),
        body_text,
    ) or re.search(
        ('n[uú]mero' if field == 'numero' else 'car[aá]tula')
        + r'.{0,80}(falta|obligatori|complet|requerid)',
        body_text,
    )
    assert (validity.get('missing') and validation_message) or server_message, (
        f'SIGEX no indicó que {field} es obligatorio'
    )
    assert 'mesa_entrada.php' in expedientes.driver.current_url
    expedientes.search(numero)
    assert not expedientes.exact_rows(numero), (
        f'SIGEX registró el expediente aunque faltaba {field}'
    )


@pytest.mark.parametrize(('case_id', 'invalid_number'), [
    pytest.param('CP09', 'AUTO/@#$-CARACTER-INVALIDO', id='CP09'),
    pytest.param('CP10', 'formato-cualquiera-incorrecto', id='CP10'),
])
def test_numero_causa_formato_invalido(expedientes, numero, case_id, invalid_number):
    expedientes.new()
    expedientes.fill(numero)
    expedientes.set_text(expedientes.NUMBER, f'{invalid_number}-{numero}')
    number_field = expedientes.visible(expedientes.NUMBER)
    submitted_number = number_field.get_attribute('value')
    assert submitted_number, 'No se pudo ingresar el numero invalido de prueba'

    # Guardar la validación del navegador antes del submit: SIGEX puede redirigir
    # al detalle si acepta el valor, y en esa pantalla el campo ya no existe.
    validity_before_save = expedientes.validity(expedientes.NUMBER)
    native_message = (number_field.get_attribute('validationMessage') or '').lower()
    expedientes.save()
    body_text = expedientes.visible(expedientes.BODY).text.lower()
    rejected_format = (
        validity_before_save.get('patternMismatch') and bool(native_message)
    ) or (
        re.search(r'(formato|caracter|n[uú]mero).{0,80}(inv[aá]lid|incorrect|no v[aá]lid)', body_text)
        or re.search(r'(inv[aá]lid|incorrect|no v[aá]lid).{0,80}(formato|caracter|n[uú]mero)', body_text)
    )

    expedientes.search(submitted_number)
    assert not expedientes.exact_rows(submitted_number), (
        f'{case_id}: SIGEX permitió registrar el número de causa inválido'
    )
    assert rejected_format, (
        f'{case_id}: SIGEX no mostró una validación de formato o caracteres inválidos'
    )


def test_CP13_expediente_duplicado(creado):
    page, number = creado
    page.new()
    page.fill(number)
    page.save()
    page.search(number)
    assert len(page.exact_rows(number)) == 1, (
        'SIGEX permitió registrar dos expedientes con el mismo número de causa'
    )
