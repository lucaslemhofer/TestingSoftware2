# Casos automatizados de SIGEX

La suite contiene únicamente los 17 casos acordados. Cada prueba se informa como
`PASSED` cuando cumple su criterio de aprobado, `FAILED` cuando SIGEX permite la
acción que debería impedir o no permite la acción esperada, y `ERROR` cuando no
se puede completar la prueba por un problema de preparación, acceso o ejecución.

| ID | Caso de prueba | Se considera aprobado cuando… |
|---|---|---|
| CP01 | Registrar expediente correctamente | Se cargan manualmente los campos, se registra el expediente y aparece guardado. |
| CP02 | Registrar expediente sin número de causa | SIGEX muestra que falta el número y no registra el expediente. |
| CP03 | Registrar expediente sin carátula | SIGEX muestra que falta la carátula y no registra el expediente. |
| CP09 | Número de causa con caracteres especiales inválidos | SIGEX muestra una validación de formato/caracteres y no registra el expediente. |
| CP10 | Número de causa con formato incorrecto | SIGEX muestra una validación de formato y no registra el expediente. |
| CP13 | Número de causa duplicado | No se guarda un duplicado y queda una sola coincidencia. |
| CP17 | Pase a responsable válido | El pase queda registrado y el responsable actual es el destino elegido. |
| CP18 | Pase sin responsable | El pase no se registra y no cambia el responsable ni el historial. |
| CP27 | Borrador en expediente asignado | El borrador se guarda con contenido y asociado al expediente asignado. |
| CP28 | Borrador sin expediente seleccionado | Desde la lista sin abrir una causa no aparece el formulario contextual para crear borradores. |
| CP31 | Continuar edición de borrador | Se puede editar y los cambios persisten al reabrirlo. |
| CP35 | Generar nueva versión | La edición crea una versión adicional con el contenido nuevo. |
| CP36 | Conservar versión original | Las versiones previas permanecen en el historial después de nuevas ediciones. |
| CP38 | Mostrar contenido entre versiones | La comparación muestra el texto original y el modificado. |
| CP42 | Buscar expediente existente | La búsqueda devuelve exactamente el expediente correspondiente. |
| CP43 | Buscar número inexistente | La búsqueda no devuelve expedientes. |
| CP47 | Buscar combinando número y parte | Ambos filtros juntos devuelven la coincidencia esperada. |

## Alcance y ejecución

La carga del expediente de prueba se hace escribiendo los campos mediante Selenium;
no se usa el botón **Completar para prueba**. Los expedientes, pases y borradores
sintéticos creados por las pruebas permanecen en SIGEX.

CP09 y CP10 verifican una regla de rechazo que el usuario espera de SIGEX: si el
número inválido se guarda o no aparece una validación de formato/caracteres, el
caso falla. CP28 verifica que desde la lista, sin seleccionar una causa, no esté
disponible el formulario contextual de borradores.

Para ver la lista exacta de pruebas recopiladas:

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q
```
