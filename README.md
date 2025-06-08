# SVGCreator

SVGCreator es una aplicación de escritorio con interfaz gráfica (GUI) diseñada para ayudar en la creación de archivos SVG compuestos, combinando una imagen de fondo en formato SVG con una imagen de primer plano en formato PNG (con transparencia).

## Funcionalidades Principales (Objetivo)

El objetivo principal de la aplicación es permitir al usuario:

1.  **Cargar Imágenes:**
    *   Seleccionar una **imagen de primer plano** (formato PNG, idealmente con transparencia).
    *   Seleccionar un **archivo de fondo** (formato SVG, que ya contiene curvas y colores).
2.  **Optimización de Imagen de Primer Plano:**
    *   Si la imagen de primer plano PNG supera un tamaño de archivo específico (actualmente 700 KB), la aplicación intentará optimizarla utilizando `pngquant` para reducir su tamaño, ajustando iterativamente la calidad para acercarse al tamaño objetivo sin una pérdida visual excesiva.
3.  **Selección de Carpeta de Salida:**
    *   Permitir al usuario elegir una carpeta donde se guardarán los archivos procesados y el SVG final.
4.  **Generación de SVG Compuesto:**
    *   Crear un nuevo archivo `.svg` que:
        *   Incorpore el contenido del archivo SVG de fondo (sus curvas, colores, etc.).
        *   Incruste la imagen de primer plano PNG optimizada (codificada en Base64) encima del contenido del fondo.
        *   Las dimensiones del SVG final se basarán, por defecto, en las dimensiones de la imagen de primer plano.

## Estado Actual del Proyecto (Junio 2025)

Actualmente, la aplicación cuenta con las siguientes funcionalidades implementadas:

*   **Interfaz Gráfica de Usuario (GUI):**
    *   Desarrollada con `customtkinter`.
    *   Permite cargar la imagen de primer plano (PNG).
    *   Permite cargar el archivo de fondo (SVG).
    *   Permite seleccionar una carpeta de salida.
    *   Muestra mensajes de estado básicos.
*   **Optimización de Imagen de Primer Plano:**
    *   Se ha implementado la lógica para llamar al ejecutable `pngquant.exe`.
    *   Realiza una optimización iterativa ajustando el rango de calidad para intentar alcanzar un tamaño de archivo objetivo (aproximadamente 700 KB) si la imagen original es mayor.
    *   La imagen optimizada (o una copia de la original si no se requiere/logra optimización) se guarda en un subdirectorio (`optimized_foreground_image`) dentro de la carpeta de salida seleccionada por el usuario.
*   **Generación de SVG (Parcial):**
    *   Se ha creado el módulo `svg_generator.py` con una función `create_final_svg`.
    *   Esta función actualmente intenta:
        *   Crear un nuevo documento SVG.
        *   **Incrustar el contenido del SVG de fondo:** Se está utilizando `xml.etree.ElementTree` para parsear el SVG de fondo y `svgwrite.xml.Raw` para intentar inyectar sus elementos (incluyendo `<defs>` y `<style>`) en el SVG principal. Esta parte puede necesitar más pruebas y refinamiento para manejar SVGs de fondo complejos de manera robusta.
        *   **Incrustar la imagen PNG de primer plano:** La imagen PNG optimizada se codifica en Base64 y se añade como un elemento `<image>` con un Data URI.
    *   El SVG final se guarda en la carpeta de salida seleccionada por el usuario.

## Tecnologías y Herramientas Utilizadas

*   **Lenguaje:** Python
*   **GUI:** `customtkinter`
*   **Manejo de Imágenes (PNG):** `Pillow` (PIL Fork)
*   **Optimización de PNG:** `pngquant` (ejecutable externo llamado vía `subprocess`)
*   **Generación de SVG:** `svgwrite`
*   **Parseo de XML/SVG:** `xml.etree.ElementTree`
*   **Entorno Virtual:** `venv`
*   **Control de Versiones:** Git y GitHub

## Próximos Pasos y Funcionalidades Pendientes

1.  **Refinar la Incrustación del SVG de Fondo:**
    *   Mejorar la lógica en `svg_generator.py` para una incrustación más robusta del contenido del SVG de fondo, asegurando que los estilos (CSS, clases, `<defs>`) se transfieran y apliquen correctamente. Esto podría implicar una recreación más detallada de los elementos del SVG de fondo usando los métodos de `svgwrite` o explorar bibliotecas especializadas en manipulación/fusión de SVG si es necesario.
    *   Considerar cómo manejar los `viewBox`, `width`, y `height` del SVG de fondo al incrustarlo, y cómo deberían relacionarse con el SVG principal.
2.  **Mejorar la Interfaz de Usuario:**
    *   Añadir previsualizaciones de las imágenes cargadas.
    *   Proporcionar más información y control sobre el proceso de optimización (ej. permitir al usuario ajustar el nivel de calidad o el tamaño objetivo).
    *   Mejorar los mensajes de error y de progreso.
    *   Opción para definir explícitamente las dimensiones del SVG final.
    *   Opción para definir la posición (x, y) de la imagen de primer plano sobre el fondo.
3.  **Manejo de Errores y Excepciones:**
    *   Fortalecer el manejo de errores en todos los módulos.
4.  **Empaquetado de la Aplicación:**
    *   Investigar y implementar el empaquetado de la aplicación (ej. con PyInstaller o cx_Freeze) para crear un ejecutable distribuible para Windows, incluyendo `pngquant.exe`.
5.  **Pruebas Exhaustivas:**
    *   Probar con una variedad más amplia de imágenes PNG y archivos SVG de fondo para identificar y corregir problemas.

## Cómo Contribuir (Si fuera un proyecto abierto)

*(Esta sección es opcional para tu proyecto personal, pero es estándar en proyectos de código abierto)*
Actualmente, este es un proyecto personal. Si en el futuro se abriera a contribuciones, se detallarían aquí las guías para hacerlo.

## Licencia (Si aplica)

*(Añadir información de licencia si es relevante)*