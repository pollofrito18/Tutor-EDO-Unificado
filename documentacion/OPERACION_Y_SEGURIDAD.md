# Operación y seguridad

## Implementación actual

La aplicación se inicia en `127.0.0.1` para uso local. Las cuentas viven en la base seleccionada. El registro no crea administradores, y las cuentas no pueden leer resultados, conversaciones, notificaciones o progreso ajenos desde la aplicación.

- Contraseñas de 12 a 128 caracteres, procesadas con Argon2id mediante `argon2-cffi`. Se guarda el hash y se permite su actualización al iniciar sesión. Referencia: [Argon2](https://argon2-cffi.readthedocs.io/en/stable/howto.html).
- Sesiones opacas aleatorias en memoria de Streamlit; la base solo conserva SHA-256 del token y su vencimiento de 12 horas. Cambiar la contraseña revoca todas las sesiones. Cerrar sesión limpia el estado de interfaz.
- Las operaciones de persistencia reciben el token y resuelven su propietario en el servidor. No aceptan un id de usuario elegido por un formulario.
- Ocho intentos de acceso por nombre de usuario en 15 minutos; 30 intentos de registro por instalación y hora; 20 consultas al tutor por usuario y hora; 60 acciones de cálculo por usuario cada diez minutos. Los contadores son persistentes. Los intentos fallidos de tutor también consumen cuota.
- Consultas SQLAlchemy parametrizadas, claves foráneas activas, índices y restricciones de unicidad.
- Parser matemático por lista de sintaxis AST. No se pasa texto de usuario a `eval`, `exec`, `sympify` o `parse_expr`. El código generado por `lambdify` solo recibe expresiones ya construidas por el parser.
- Expresiones de hasta 350 caracteres con límites de nodos, profundidad y exponentes; cálculos en procesos detenidos a los 18 segundos; hasta dos procesos de cálculo simultáneos por servidor Streamlit. El worker no recibe la clave NVIDIA ni DATABASE_URL en su entorno.
- No se muestran credenciales ni trazas de conexión en errores de la aplicación. No se ejecuta código devuelto por NVIDIA. El endpoint remoto está fijado en código, usa HTTPS, tiempo de espera y no sigue redirecciones.
- `.env`, bases, copias y entornos están excluidos de Git. Los archivos SQLite se crean con permisos de lectura/escritura del propietario donde el sistema operativo soporta esos permisos.

No se presenta esta lista como auditoría integral ni como defensa frente a todo abuso. La instalación pública requiere configurar HTTPS, acceso al servidor, límites de red, copias y monitoreo, y validar el entorno. Los límites por nombre de usuario pueden usarse para bloquear temporalmente un nombre; no sustituyen controles de red. No hay MFA ni recuperación por correo en esta edición.

## SQLite

Se selecciona automáticamente cuando DATABASE_URL está vacío. Es adecuado para la instalación local del proyecto. Los archivos WAL/SHM son gestionados por SQLite. Para respaldar usa su API de backup mediante el comando incluido, en vez de copiar solo el archivo principal mientras la base está activa.

```powershell
.\.venv\Scripts\python.exe mantenimiento.py respaldo
```

Restauración:

1. Detén la aplicación con Ctrl+C.
2. Conserva una copia de la carpeta `datos` actual.
3. Crea una carpeta vacía, por ejemplo `datos_restaurados`, y copia allí el respaldo renombrándolo como `tutor.sqlite3`.
4. Añade en `.env` una ruta absoluta, por ejemplo `TUTOR_DATA_DIR=C:/Proyectos/Tutor_EDO_Unificado/datos_restaurados`. Deja DATABASE_URL vacío.
5. Inicia la aplicación y comprueba que aparezcan tus resultados.

Restaurar a una carpeta nueva evita mezclar un respaldo con archivos WAL de otra base. El respaldo contiene hashes de cuentas, tokens y datos personales: protégelo igual que la base original. La copia integral se verifica automáticamente con `PRAGMA integrity_check`.

## PostgreSQL opcional

El motor de persistencia acepta una URL de [SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/engines.html). Las cuentas de SQLite no se transfieren automáticamente al seleccionar otra base.

Puedes usar un PostgreSQL existente o el archivo Compose incluido. Este último necesita Docker instalado:

```powershell
$env:POSTGRES_PASSWORD = Read-Host 'Contraseña privada para PostgreSQL'
docker compose -f compose.postgres.yml up -d
```

Configura `.env` con los datos de esa base:

```dotenv
DATABASE_URL=postgresql+psycopg://tutor_edo:CLAVE_CODIFICADA@localhost:5432/tutor_edo
```

Codifica los caracteres especiales de la contraseña según las reglas de URL. La clave anterior es un marcador, no una credencial incluida. El servicio solo expone PostgreSQL en localhost. No ejecutes `docker compose down -v` si quieres conservar el volumen.

```powershell
.\.venv\Scripts\python.exe mantenimiento.py migrar
```

El inicio de la aplicación aplica también las migraciones. En una instalación con varios procesos, ejecuta las migraciones una vez antes de iniciar los procesos. Si DATABASE_URL explícita falla, no se crea otra base silenciosamente.

`ESQUEMA_POSTGRESQL.sql` es el DDL generado por la revisión inicial con el dialecto PostgreSQL. Su generación fue validada; no se ejecutó contra un servidor PostgreSQL real en esta entrega. Usa Alembic para administrar las versiones, sin aplicar repetidamente ese SQL a una base existente.

Para respaldar PostgreSQL usa `pg_dump` con sus mecanismos de credenciales, sin poner la clave en un comando que quede en el historial. Consulta la [documentación de respaldos PostgreSQL](https://www.postgresql.org/docs/17/backup-dump.html). Verifica también la restauración en una base separada antes de depender de un respaldo.

## Escalabilidad y mantenimiento

Esta es una aplicación modular de un proceso, adecuada como base académica. El almacenamiento y los cálculos están separados de la interfaz. Para crecer: emplear PostgreSQL, paginar consultas del historial, trasladar trabajos pesados a una cola y validar las sesiones/conexiones de varios procesos. La versión actual limita las vistas y exportaciones personales a los registros indicados en pantalla; conserva los registros antiguos en la base.

La base se comparte entre las sesiones de esta instalación; no se sincroniza entre computadoras distintas sin un servidor común. No se almacena la clave NVIDIA por usuario: la configura el responsable del servidor. No envíes información privada innecesaria en las preguntas.
