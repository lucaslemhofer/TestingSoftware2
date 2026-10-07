# Testing automatizado de SIGEX

Proyecto Python + Selenium + pytest con Page Object Model en pages/. La suite
contiene únicamente los 17 casos CP01, CP02, CP03, CP09, CP10, CP13, CP17, CP18,
CP27, CP28, CP31, CP35, CP36, CP38, CP42, CP43 y CP47.

## Ejecutar en PowerShell, desde esta carpeta

El entorno .venv y el archivo .env existentes se conservan.

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q
.\.venv\Scripts\python.exe -m pytest --read-only
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest -k CP01
```

La ejecución completa crea expedientes AUTO-, pases y sentencias sintéticas.
Cada prueba prepara sus propios datos y no modifica expedientes preexistentes.
Los datos creados permanecen en SIGEX: no se realiza borrado automático.
--read-only omite los casos capaces de crear datos, incluidas validaciones negativas.

## Credenciales

.env es privado y está excluido de Git. No pegues credenciales en los tests.
SIGEX_USER y SIGEX_PASSWORD deben corresponder a Mesa de Entrada o una cuenta
con permiso de alta. Para borradores/versiones se usan SIGEX_RELATOR_USER y
SIGEX_RELATOR_PASSWORD, de Secretario Relator.
SIGEX_USE_DEMO=true utiliza exclusivamente las credenciales que la pantalla
publica para esos dos roles. No se guardan en código. Las variables de entorno
tienen precedencia sobre .env. Si faltan cuentas requeridas, el caso se omite;
si están configuradas pero el acceso falla, se informa ERROR.

En una instalación nueva, crear .venv e instalar requirements.txt. Copiar
.env.example a .env solo si este último todavía no existe.

## Estructura y evidencias

- pages/: selectores y acciones de login, expedientes y documentos.
- tests/: únicamente los 17 casos indicados arriba.
- data/casos.json y docs/MATRIZ.md: casos y criterios de aprobado acordados.
- reports/report.html: reporte autónomo con capturas integradas.
- reports/results.xml: resultados para integración continua.
- screenshots/: capturas ante fallos de preparación o prueba con navegador activo.
- docs/backups/: respaldo del código anterior, sin .env ni entorno virtual.

Los campos se ocultan temporalmente antes de capturar y luego se restauran.
Se redactan credenciales en errores y salidas capturadas. Las capturas pueden
contener información visible de la aplicación; revisarlas antes de compartir.

PASSED = se cumplió el criterio de aprobado; FAILED = el resultado observado
contradice ese criterio; ERROR = no se pudo completar la ejecución por un
problema de acceso, preparación o entorno. --read-only omite casos que crean o
modifican datos.

Los campos del expediente se completan manualmente mediante Selenium; no se usa
el botón Completar para prueba. Los datos sintéticos permanecen en SIGEX.
