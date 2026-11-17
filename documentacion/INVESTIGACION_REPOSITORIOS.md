# Repositorios y patrones utilizados

Se integraron los patrones útiles de la investigación previa en esta única aplicación. Las implementaciones de interfaz, autorización, ejemplos y adaptadores son propias; las bibliotecas se consumen como dependencias.

| Fuente primaria | Qué aporta | Aplicación en este proyecto |
| --- | --- | --- |
| [SymPy](https://github.com/sympy/sympy) | Álgebra, derivadas, integrales y verificación simbólica | nucleo/motor.py y comprobación de los modelos |
| [SymPy Gamma](https://github.com/sympy/sympy_gamma) | Organización de explicaciones matemáticas mediante reglas | Adaptador propio modulos/integrales.py sobre manualintegrate de SymPy |
| [SciPy](https://github.com/scipy/scipy) | Integradores numéricos | solve_ivp como aproximación de referencia |
| [Plotly.py](https://github.com/plotly/plotly.py) | Gráficas interactivas | Curvas 2D, superficies y trazas 3D, exportación HTML |
| [NVIDIA GenerativeAIExamples](https://github.com/NVIDIA/GenerativeAIExamples) | Ejemplos de integración de servicios de IA | Patrón de cliente remoto; adaptador requests ajustado a este proyecto |
| [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) | Mapeo de datos y transacciones | Capa unificada de cuentas y datos |
| [PyDy](https://github.com/pydy/pydy) | Modelado de dinámica multivariable | Referencia para ampliaciones; no es dependencia ni se presenta como funcionalidad implementada |

La investigación previa conserva su instantánea en `repositorios.json`; los contadores de popularidad no son una medida de corrección. Las licencias de referencia se conservan en `licencias_referencia/`. No se incorpora un repositorio de terceros completo ni se copia su frontend antiguo.

Referencias de API consultadas para la integración:

- [Surface y gráficas 3D de Plotly](https://plotly.com/python/3d-surface-plots/).
- [API de modelos de NVIDIA](https://docs.api.nvidia.com/nim/reference/llm-apis).
- [Audio de Streamlit](https://docs.streamlit.io/develop/api-reference/media/st.audio).
- [Configuración de motores SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/engines.html).
- [Argon2 para contraseñas](https://argon2-cffi.readthedocs.io/en/stable/howto.html).

Actualizar una biblioteca exige revisar sus cambios y ejecutar las pruebas. No se asume que código antiguo de un repositorio sea compatible con las versiones instaladas.
