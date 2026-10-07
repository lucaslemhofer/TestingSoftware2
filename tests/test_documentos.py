import pytest

pytestmark = pytest.mark.writes


def test_CP27_borrador_asignado(borrador):
    page, title, content, number = borrador
    assert page.content() == content
    assert number in page.visible(page.BODY).text


def test_CP28_borrador_sin_expediente(authenticate):
    # Desde la lista, sin abrir un expediente, no debe estar disponible el
    # formulario contextual para crear un borrador.
    expediente_page = authenticate('Secretario Relator')
    expediente_page.navigate_click(expediente_page.LIST)
    assert not expediente_page.driver.find_elements(
        'css selector', '#nuevo-borrador'
    ), 'SIGEX mostró el formulario de borrador sin un expediente seleccionado'


def test_CP31_continuar_edicion(borrador):
    page, title, content, _ = borrador
    updated = content + ' actualizado'
    page.edit(updated, 'Cambio de prueba')
    page.open_document(title)
    assert page.content() == updated, 'SIGEX no guardó los cambios del borrador'


def test_CP35_generar_nueva_version(borrador):
    page, title, content, number = borrador
    before = page.versions()
    updated = 'Texto modificado ' + number
    page.edit(updated, 'Nueva version ' + number)
    page.open_document(title)
    after = page.versions()
    assert len(after) == len(before) + 1, 'No se registró una nueva versión'
    assert page.content() == updated, 'La nueva versión no contiene el texto editado'


def test_CP36_conservar_version_original(borrador):
    page, title, _, number = borrador
    original_versions = page.versions()
    page.edit('Primera modificación ' + number, 'Primera versión nueva')
    page.open_document(title)
    after_first = page.versions()
    assert len(after_first) == len(original_versions) + 1

    page.edit('Segunda modificación ' + number, 'Segunda versión nueva')
    page.open_document(title)
    after_second = page.versions()
    assert len(after_second) == len(after_first) + 1
    assert after_second[1:] == after_first, (
        'La edición sobrescribió o eliminó versiones anteriores'
    )


def test_CP38_visualizar_contenido_modificado(borrador):
    page, title, _, number = borrador
    updated = 'Contenido cambiado ' + number
    page.edit(updated, 'Cambio visible ' + number)
    page.open_document(title)
    diff = page.latest_diff()
    diff_lower = diff.lower()
    assert 'agregado' in diff_lower and 'eliminado' in diff_lower, (
        'No se abrió la comparación de versiones'
    )
    assert 'original' in diff_lower and 'cambiado' in diff_lower and number in diff, (
        'La comparación no deja ver las partes del contenido que cambiaron'
    )
