# Diseño y accesibilidad

Objetivo de diseño: WCAG 2.2 AA. No se afirma conformidad completa ni certificación. La [recomendación de W3C](https://www.w3.org/TR/WCAG22/) requiere evaluar criterios sobre páginas y procesos completos; una paleta correcta no es suficiente.

Implementado: etiquetas visibles; texto configurable entre 16 y 22 px; LaTeX como contenido renderizado; SVG decorativos ocultos a lectores de pantalla; foco visible; colores acompañados de nombres, trazos o mensajes; tabla alternativa de las gráficas; vistas de cámara predefinidas; avisos visuales junto al sonido; sonido desactivado inicialmente y volumen ajustable.

Contraste calculado para los colores propios sobre fondo blanco:

| Uso | Color | Relación |
| --- | --- | --- |
| Texto principal | #14243E | 15.54:1 |
| Texto secundario | #41516A | 8.05:1 |
| Azul | #1746B6 | 8.11:1 |
| Rojo | #B91C1C | 6.47:1 |
| Amarillo oscuro | #946B00 | 4.81:1 |

Se usan tonos oscuros de los colores primarios para mantener legibilidad. Estos valores no representan una auditoría de todos los estados de componentes de Streamlit y Plotly. Las superficies tienen una escala de intensidad y una curva identificada con su nombre.

Verificación pendiente en el equipo final: navegación completa con Tab/Enter, lector de pantalla y pronunciación de fórmulas; zoom del navegador a 200%; móvil y reflujo; WebGL con ratón/táctil; reproducción de sonido bajo las políticas del navegador. El idioma del contenido es español; hay que revisar también los textos y atributos que generan las bibliotecas antes de declarar conformidad integral.
