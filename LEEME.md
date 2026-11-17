# Tutor EDO Unificado

Una sola aplicación para aprender, resolver ecuaciones diferenciales y explorar modelos en 2D y 3D. Integra cuentas, resultados, aprendizaje, tutor NVIDIA y notificaciones con la misma base de datos.

## Abrir en Windows

1. Extrae el ZIP completo. No ejecutes archivos dentro del ZIP.
2. Instala Python 3.12 con el lanzador `py` si todavía no lo tienes.
3. Abre `instalar_windows.bat` y espera el mensaje de instalación terminada.
4. Abre `iniciar_windows.bat`.
5. En el navegador entra a `http://localhost:8501`, crea una cuenta e inicia sesión.

También puedes usar PowerShell dentro de la carpeta del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

No hace falta activar el entorno virtual. Estos comandos usan directamente su Python y evitan problemas de políticas de ejecución de PowerShell. Mantén abierta la terminal mientras utilices la aplicación; Ctrl+C la detiene.

En Linux o macOS, crea el entorno con `python3.12 -m venv .venv`, instala con `.venv/bin/python -m pip install -r requirements.txt` y ejecuta `.venv/bin/python -m streamlit run app.py`.

## Preparar una memoria USB para usar sin internet

En la PC donde preparas el proyecto, ejecuta `crear_portable_windows.bat` con internet. Para crear un instalador único de Windows, instala Inno Setup 6 en esa PC y ejecuta `crear_instalador_windows.bat`. El resultado es `Instalador_TutorEDO_Windows_x64.exe`. Copia ese instalador a la memoria USB; en la PC de destino Windows x64, ábrelo, termina la instalación e inicia Tutor EDO desde el acceso directo. No se requiere internet ni Python en el destino. Si prefieres no instalar, también puedes copiar la carpeta portable completa y ejecutar `TutorEDO.exe` desde ella.

El paquete no copia `.env` ni la base de datos de esta PC: en el destino se crea una base nueva y una cuenta nueva. El tutor NVIDIA requiere internet y una clave propia, por lo que no estará disponible sin conexión; el solucionador, las lecciones, los modelos y el historial local sí funcionan.

## Qué incluye

| Apartado | Comportamiento implementado |
| --- | --- |
| Cuenta | Registro, inicio y cierre de sesión, nombre visible, cambio de contraseña y revocación de sesiones |
| Resolver | EDO de primer orden: separables, lineales, exactas y factores integrantes de x o y; EDO lineales de segundo orden con coeficientes constantes; condiciones iniciales, pasos LaTeX y verificación |
| Comparar | Selección de otro método aplicable, Euler, RK4 y referencia SciPy con tablas y etapas |
| Modelos y 3D | Enfriamiento, crecimiento exponencial, logística, velocidad con resistencia y mezcla en tanque |
| Gráficas | Rotación, zoom, vistas de cámara, colores, tasas, referencias, condiciones iniciales y resolución editables |
| Aprender | Diez lecciones, siete ejercicios con respuesta libre, pistas, errores frecuentes y aplicaciones cotidianas |
| Integrales | Árbol de reglas, antiderivada y comprobación; identifica explicaciones incompletas |
| Historial | Guarda entradas, resultados y escenarios; recupera ecuaciones o parámetros para volver a trabajar |
| Tutor NVIDIA | Conversaciones generales o ligadas a un resultado, contexto y mensajes persistidos |
| Notificaciones | Bandeja de leídas/no leídas; sonidos opcionales con volumen y eventos configurables |
| Preferencias | Texto de 16 a 22 px, color preferido, sonidos desactivados inicialmente |
| Exportar | JSON de resultados y datos personales, Markdown de procedimientos, CSV y HTML de gráficas; PNG desde la barra de Plotly |
| Persistencia | SQLite listo al primer inicio, SQLAlchemy, migración Alembic y configuración opcional PostgreSQL |

Todos los archivos que necesitas para ejecutar esta versión están en esta carpeta. No debes combinar los ZIP anteriores ni copiar los módulos de referencia. Las dependencias se descargan al instalar `requirements.txt`.

## Primer recorrido sugerido

1. En **Aprender**, completa «Variables: qué cambia y respecto a qué».
2. En **Resolver**, envía `y'=2*x*y`, con x inicial 0 e y inicial 1. La solución particular es `exp(x^2)`.
3. Prueba también `y''+y=0`, con x inicial 0, y inicial 1 y y' inicial 0. La respuesta es `cos(x)`.
4. Calcula la tabla numérica del caso de primer orden con x final 1 y compara Euler, RK4 y SciPy.
5. En **Modelos y 3D**, selecciona enfriamiento. Con T0=80, ambiente=25, k=0.1 y tiempo final 10, el resultado es aproximadamente 45.23 °C.
6. Guarda el escenario. Recupéralo desde **Mi historial** y cambia sus parámetros.
7. Activa los sonidos en **Ajustes**, elige los eventos y usa **Probar sonido**.
8. Configura NVIDIA para consultar un paso del procedimiento desde el resultado.

## Activar el tutor NVIDIA

El motor matemático, las gráficas, las cuentas y el aprendizaje funcionan sin NVIDIA. Para el tutor necesitas una clave válida y un modelo habilitado en tu cuenta.

1. Copia `.env.example` como `.env` dentro de la carpeta del proyecto.
2. Completa localmente:

```dotenv
NVIDIA_API_KEY=tu_clave_privada
NVIDIA_MODEL=meta/llama-3.1-8b-instruct
```

El nombre anterior es un ejemplo de la [referencia de modelos NVIDIA](https://docs.api.nvidia.com/nim/reference/llm-apis); utiliza un modelo habilitado para tu cuenta. No incluyas la clave en archivos que compartas ni la pegues en el chat del tutor. Reinicia Streamlit después de cambiar `.env`.

La conexión usa el endpoint oficial `https://integrate.api.nvidia.com/v1/chat/completions`. Esta entrega prueba el adaptador con respuestas simuladas y errores controlados. No se realizó una llamada autenticada real porque no se proporcionaron credenciales.

Al enviar una pregunta se comparten con NVIDIA el texto, el resultado asociado y hasta seis mensajes anteriores. Las explicaciones de IA se distinguen de las identidades que comprueba SymPy. El proveedor puede aplicar límites o cargos de acuerdo con la cuenta.

## Datos y copias de seguridad

Sin `DATABASE_URL`, la aplicación crea `datos/tutor.sqlite3`. No borres esa carpeta si quieres conservar cuentas y resultados. No incluye cuentas ni contraseñas predefinidas.

```powershell
.\.venv\Scripts\python.exe mantenimiento.py respaldo
```

La copia se guarda en `backups/` y se comprueba su integridad. Consulta `documentacion/OPERACION_Y_SEGURIDAD.md` para restaurar y usar PostgreSQL.

## Comprobar la instalación

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s pruebas -v
```

También puedes abrir `probar_windows.bat`. Los tests usan bases temporales y respuestas simuladas de NVIDIA; no llaman al proveedor ni modifican tu base personal.

## Alcance y límites que conviene conocer

- No promete resolver cualquier ecuación. El motor explica las EDO de primer orden indicadas y las EDO lineales de segundo orden con coeficientes constantes. La aproximación numérica es para primer orden. No incluye sistemas, coeficientes variables ni derivadas parciales, y algunas fuerzas pueden conservar integrales no elementales.
- Una solución implícita o con integrales pendientes se identifica expresamente. La comprobación de identidad no demuestra unicidad ni el dominio máximo de existencia.
- La gráfica 3D representa familias de los cinco modelos implementados: tiempo, condición inicial y resultado. Las EDO escritas libremente tienen su exploración numérica 2D.
- El laboratorio de integrales supone x>0 y conserva las restricciones de la entrada. No traduce cada regla posible de SymPy a un desarrollo completo.
- El navegador debe disponer de WebGL para el visor 3D. La tabla y la curva 2D permiten estudiar los valores por otra vía. El HTML exportado incluye Plotly y puede abrir sin conexión.
- La cámara elegida entre las tres vistas se guarda; los movimientos manuales de cámara no se persisten en la base.
- El navegador puede bloquear el sonido automático. Cada evento conserva un mensaje visible.
- SQLite y los recorridos de aplicación fueron probados. Se incluye el esquema SQL para PostgreSQL y sus migraciones; la conexión a un servidor PostgreSQL real requiere validación en el entorno donde se instale.
- La interfaz busca WCAG 2.2 AA, pero no se declara conformidad completa ni certificación. Las pruebas de navegador, lector de pantalla y dispositivos finales están descritas en la documentación.

## Archivos principales

| Ruta | Responsabilidad |
| --- | --- |
| `app.py` | Una sola entrada, navegación y sesión |
| `interfaz/` | Vistas, componentes, SVG, fórmulas y estilo |
| `nucleo/` | Parser cerrado, métodos simbólicos y aproximación numérica |
| `modulos/` | Lecciones, práctica, integrales, cinco modelos y cliente NVIDIA |
| `datos_app/` | Esquema, autenticación, autorización y casos de persistencia |
| `migraciones/` | Evolución versionada del esquema |
| `servicio.py`, `worker.py` | Procesos de cálculo con límite de tiempo y concurrencia |
| `pruebas/` | Matemáticas, seguridad, persistencia y recorridos de interfaz |
| `documentacion/` | Arquitectura, uso, referencias, seguridad y validación |

El proyecto usa Python, CSS y SVG definidos en código; no contiene emojis ni imágenes generadas para el diseño.
