# Requerimientos V2 - Delta Update

Este documento sirve como un anexo de actualización a los requerimientos originales del **Personal Library Tracker**. Se documentan exclusivamente las nuevas funcionalidades añadidas en la Versión 2.

## 1. Módulo de Autocompletado por ISBN (Google Books API)
Para facilitar la carga manual de libros físicos o aquellos que no dispongan de archivo ePub, el sistema integrará un buscador por ISBN.

- **Frontend:** 
  - Inclusión de un campo de entrada para ISBN (10 o 13 dígitos) en el formulario de creación de libros.
  - Botón de acción "Buscar".
  - Al hacer clic, el cliente (JavaScript Vanilla) ejecutará una petición asíncrona a la API pública de Google Books: `https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}`.
  - Se extraerá del JSON de respuesta: Título, Autor, Editorial, Año de publicación, y la URL de la portada.
  - Los campos del formulario se autocompletarán instantáneamente (sin recarga de página).
  - Manejo visual de errores en caso de que el ISBN no sea encontrado o la red falle.
- **Backend:** 
  - La API interna de creación y actualización (`/api/books`) deberá ser capaz de procesar URLs externas de portada además de las subidas locales.

## 2. Sistema de Puntuación (Rating 1-5)
Para añadir valor crítico a la colección, se incorpora una calificación obligatoria.

- **Base de Datos (SQLite):**
  - Expansión de la tabla `books` para incluir la columna `rating INTEGER NOT NULL DEFAULT 1`.
  - Actualización de las consultas CRUD en `models.py` para leer y escribir la calificación.
- **Frontend / UI:**
  - **Formulario (`book_form.html`):** Inclusión de un selector de calificación (estrellas o radio buttons del 1 al 5).
  - **Estantería / Dashboard (`index.html`):** Visualización del rating de cada libro (por ejemplo, con iconos de estrella) de forma destacada en las tarjetas.
  - **Vista Detalle (`book_detail.html`):** Mostrar claramente la calificación otorgada.
- **Backend:**
  - Validación en la capa de servicios para asegurar que el `rating` sea un número entero entre 1 y 5.
