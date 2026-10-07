import pytest

pytestmark = pytest.mark.writes


def test_CP17_pase_responsable_valido(movido):
    page, number, comment, actor, destination = movido
    assert page.field_value('Responsable actual') == destination
    assert comment in page.history()


def test_CP18_pase_sin_responsable(creado):
    page, _ = creado
    before = page.history()
    owner = page.field_value('Responsable actual')
    page.transfer_without_destination()

    assert page.validity(page.DESTINATION)['missing'], (
        'SIGEX permitió confirmar un pase sin responsable de destino'
    )
    page.driver.refresh()
    assert page.history() == before, 'El pase sin responsable quedó registrado'
    assert page.field_value('Responsable actual') == owner
