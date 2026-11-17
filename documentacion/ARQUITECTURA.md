# Arquitectura y ampliación

Tutor EDO tiene una sola entrada `app.py`. Las funciones educativas completas conectan vista, cálculo y persistencia; no hay aplicaciones separadas que deban iniciarse juntas.

| Funcionalidad | Vista | Lógica | Persistencia |
| --- | --- | --- | --- |
| Resolver | interfaz/ecuaciones.py | nucleo/motor.py y servicio.py | resultados, notificaciones |
| Comparar | interfaz/componentes.py | nucleo/numerico.py | resultados de tipo numerico |
| Modelos y 3D | interfaz/graficas.py | modulos/modelos.py | snapshots de grafica3d y resultados de modelo |
| Aprender | interfaz/aprendizaje.py | modulos/contenido.py, practica.py, integrales.py | progreso, intentos, resultados |
| Tutor | interfaz/espacio.py | modulos/nvidia.py | conversaciones y mensajes |
| Cuenta | app.py, interfaz/espacio.py | datos_app/almacen.py | usuarios, sesiones, limites |
| Avisos | interfaz/componentes.py | eventos posteriores a operaciones completadas | notificaciones y preferencias |

Las vistas llaman a `Almacen` con una sesión. La autorización se vuelve a comprobar dentro de cada operación. Los resultados históricos son nuevos registros con la entrada y salida de ese cálculo; recalcular no modifica los anteriores.

El resultado simbólico y el texto del tutor tienen orígenes distintos. `verificado` solo corresponde al motor y al dominio indicado. La respuesta de NVIDIA lleva `verificado_por_motor=False`. Los tests de integración de interfaz simulan el proveedor para no depender de una cuenta externa.

## Añadir una función sin duplicar el proyecto

- Nueva lección: añadir su contenido a `LECCIONES`. La interfaz genera los pasos y el almacén valida su identificador.
- Nuevo ejercicio: añadir enunciado, respuesta, pista y desarrollo a `EJERCICIOS`; comprobar además las restricciones del dominio del nuevo caso.
- Nuevo método EDO: implementar su clasificación y desarrollo en el motor, incluir nombre en METODOS y verificarlo contra soluciones independientes.
- Nuevo modelo: añadir metadatos, fórmula y evaluación a `modulos/modelos.py`, verificar la ecuación y el dato inicial y revisar unidades/rangos de los controles.
- Cambio de base: agregar una nueva revisión Alembic. No editar una revisión ya aplicada para representar un esquema posterior.

## Relaciones de datos

Usuarios tienen sesiones, resultados, progreso, intentos, conversaciones y notificaciones. Una conversación puede referenciar un resultado del mismo usuario; cada mensaje pertenece a una conversación. Las preferencias forman parte de la cuenta. Los escenarios 3D son resultados con parámetros y valores numéricos, no imágenes aisladas.

## Correspondencia académica

Se mantienen Python, SymPy y NumPy del cronograma. SciPy permite contraste numérico, Streamlit genera la interfaz y Plotly añade interacción 3D. Se incluyen métodos separables, lineales, exactos, factores integrantes de x/y y modelos, cubriendo los bloques del cronograma leído. Esto no presupone una aprobación del docente ni sustituye el informe, el video o la elección del modelo que haga el grupo.
