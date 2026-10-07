from datetime import date
from uuid import uuid4


def nuevo_expediente():
    """Datos sinteticos; formato de numero pendiente de contrastar con SIGEX."""
    return {"numero": "AUTO-" + uuid4().hex[:12],
            "caratula": "Prueba automatizada SIGEX",
            "partes": "Parte ficticia de prueba",
            "fecha": date.today().isoformat()}
