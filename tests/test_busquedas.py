import pytest


@pytest.mark.writes
def test_CP42_buscar_existente(creado):
    page, number = creado
    page.search(number)
    assert page.numbers() == [number], (
        'La búsqueda no encontró el expediente creado'
    )


def test_CP43_buscar_inexistente(expedientes, numero):
    expedientes.search(numero)
    assert expedientes.numbers() == [], (
        'La búsqueda devolvió un expediente para un número inexistente'
    )


@pytest.mark.writes
def test_CP47_buscar_combinando_numero_y_parte(creado):
    page, number = creado
    actor = 'Actor sintetico ' + number
    page.search(number, parte=actor)
    assert page.numbers() == [number], (
        'La combinación de número y parte no encontró el expediente esperado'
    )
