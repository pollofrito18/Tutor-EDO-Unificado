# Validación de la versión unificada

Fecha: 10 de septiembre de 2026. Entorno de ejecución: Linux, Python 3.12.14. Las dependencias directas utilizadas están fijadas en `requirements.txt`.

## Resultado

50 pruebas automatizadas ejecutadas, 50 aprobadas. El registro está en `RESULTADO_PRUEBAS.txt`.

| Grupo | Pruebas | Riesgo que comprueban |
| --- | ---: | --- |
| Motor existente | 27 | Métodos, condiciones iniciales, equilibrios, dominios, entradas rechazadas, integradores y procesos |
| Modelos y aprendizaje | 5 | Fórmulas de los cinco modelos, valores conocidos, iniciales, equilibrios, práctica e integral/Euler |
| Adaptador NVIDIA | 4 | Ausencia de llamada sin clave, cuerpo enviado, contexto acotado, errores HTTP/timeout y respuestas inválidas |
| Persistencia y seguridad | 9 | Hashes, cierre, expiración, aislamiento, cambio de clave, límites, migraciones, reinicio y respaldo recuperable |
| Recorridos de interfaz | 5 | Registro, acceso, solver, comparación, 3D, recuperación, aprendizaje, preferencias, notificaciones y chat |

El recorrido del tutor en interfaz usa una respuesta simulada claramente identificada en el test. Las pruebas no envían preguntas a NVIDIA. La validación matemática de los modelos combina sustitución simbólica de la fórmula y su condición inicial con valores calculados independientemente.

Se corrigió un conflicto entre claves de formularios y estado de resultados detectado durante las pruebas de práctica, integrales y comparación numérica; la batería completa pasó después de corregirlo.

## Otras comprobaciones realizadas

- Generación offline del esquema PostgreSQL desde la migración inicial.
- Auditoría de caracteres de los archivos de texto propios: no se incluyeron emojis.
- Cálculo de contraste de la paleta propia sobre blanco.
- Respaldo SQLite restaurado en una base separada y consulta de los registros recuperados.
- Compilación de los módulos Python y paquete sin credenciales, bases de datos ni entornos virtuales.

## Límites de esta evidencia

AppTest ejecuta los recorridos de Streamlit y comprueba componentes/estado, pero no reproduce el ratón ni el contexto WebGL de un navegador. No se realizó revisión visual final en Windows, lector de pantalla, prueba táctil ni escucha del sonido en el dispositivo de destino. Las políticas del navegador pueden impedir reproducción automática.

No se ejecutó una llamada real autenticada a NVIDIA ni una conexión a un servidor PostgreSQL. El cliente, el tratamiento de errores y las migraciones están implementados; deben verificarse con las credenciales y el servidor correspondientes. No se declara auditoría completa de seguridad ni conformidad WCAG certificada.

## Repetir

Dentro de la carpeta del proyecto, con las dependencias instaladas:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s pruebas -v
```

Las advertencias de Streamlit sobre `ScriptRunContext` al ejecutar AppTest no indican un error de la aplicación. Comprueba el resultado final `OK` y que el número de pruebas ejecutadas sea el esperado.
