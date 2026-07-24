<div align="center">
  <h1>📚 Personal Library Tracker</h1>
  <p><i>Un sistema web CRUD ligero, local y privado para catalogar colecciones de libros físicos y digitales.</i></p>
</div>

---

## 📑 Tabla de Contenidos

- [🎯 Propósito y Visión](#-propósito-y-visión)
- [✨ Características Principales](#-características-principales)
- [🛠️ Stack Tecnológico](#️-stack-tecnológico)
- [🚀 Instalación y Uso](#-instalación-y-uso)
- [📂 Estructura del Proyecto](#-estructura-del-proyecto)
- [🛡️ Privacidad y Seguridad](#️-privacidad-y-seguridad)

---

## 🎯 Propósito y Visión

El **Personal Library Tracker** nace de la necesidad de resolver la fragmentación en la gestión de colecciones de lectura. Diseñado para unificar el inventario de libros físicos y digitales, esta herramienta brinda total independencia de servicios externos, manteniendo tus datos 100% locales, privados y bajo tu control.

Es ideal para lectores ávidos que buscan un lugar propio para el análisis crítico, las notas filológicas o simplemente un registro riguroso de su progreso de lectura.

## ✨ Características Principales

- **📖 Ingesta Automática de ePub:** Sube un archivo `.epub` y el sistema extraerá inteligentemente los metadatos (Título, Autor, Editorial, Idioma, ISBN) y la **imagen de portada**, ahorrando tiempo valioso en la catalogación.
- **⚡ Autocompletado por ISBN:** Añade libros rápidamente ingresando su ISBN. El sistema consulta automáticamente bases de datos libres (OpenLibrary) y comerciales (Google Books) para autocompletar toda la información y descargar la portada.
- **📥 Importación Masiva (Goodreads):** Si vienes de Goodreads, puedes subir directamente tu archivo `.csv` exportado. El sistema mapeará y migrará tu biblioteca completa (incluyendo rating y estatus), omitiendo duplicados.
- **🗃️ CRUD Completo y Seguro:** Crea, lee, actualiza y elimina registros literarios con un enfoque riguroso. Toda la aplicación está fortificada contra ataques comunes (CSRF, XSS y Path Traversal).
- **📊 Estado de Lectura:** Clasifica fácilmente tu colección visualmente con estados de lectura: _No leído, Leyendo, Leído_.
- **📝 Editor de Reseñas Markdown:** Soporte nativo de Markdown para escribir reseñas extensas, análisis crítico y notas filológicas, renderizadas dinámicamente con una vista previa de doble panel y sanitizadas con DOMPurify.
- **🎨 Interfaz Moderna y Óptima:** Un diseño UI/UX limpio y minimalista optimizado mediante TailwindCSS en modo oscuro. Incluye paginación dinámica (carga bajo demanda) para garantizar un rendimiento instantáneo incluso con miles de libros.

## 🛠️ Stack Tecnológico

| Capa              | Tecnología                     | Propósito                                             |
| ----------------- | ------------------------------ | ----------------------------------------------------- |
| **Backend**       | Python 3.10+ / Flask           | Servidor web eficiente y minimalista.                 |
| **Base de Datos** | SQLite 3                       | Base de datos portable en un solo archivo (WAL mode). |
| **Seguridad**     | Flask-WTF / DOMPurify          | Prevención integral de vulnerabilidades (CSRF y XSS). |
| **Frontend**      | HTML5, TailwindCSS, Vanilla JS | UI responsiva y rápida sin builds pesados de JS.      |
| **ePub Parser**   | ebooklib / lxml                | Lectura y extracción estructurada de archivos ePub.   |
| **Markdown**      | marked.js                      | Renderizado de Markdown en el lado del cliente.       |

## 🚀 Instalación y Uso

Asegúrate de contar con **Python 3.10 o superior** instalado en tu sistema. El sistema fue construido para ser fácil de levantar sin necesidad de contenedores.

```bash
# 1. Clonar el repositorio
git clone https://github.com/luisk25k/epub-library-tracker.git
cd epub-library-tracker

# 2. Crear un entorno virtual
python -m venv venv

# 3. Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 4. Instalar las dependencias
pip install -r requirements.txt

# 5. Iniciar la aplicación en segundo plano
Iniciar_Biblioteca.bat
```

> La aplicación estará disponible localmente en tu navegador en: **`http://localhost:5000`**

## 📂 Estructura del Proyecto

El sistema está diseñado de forma modular utilizando el patrón de _Application Factory_ de Flask.

```text
epub-library-tracker/
├── app/
│   ├── __init__.py            # Inicialización y configuración de Flask
│   ├── models.py              # Definición de la BD, creación y consultas SQL CRUD
│   ├── routes.py              # Definición de endpoints de API y renderizado de Vistas
│   ├── services/
│   │   ├── book_service.py    # Lógica de negocio e integración entre modelos y parser
│   │   └── epub_parser.py     # Lógica robusta de parsing de Dublin Core y OPF
│   ├── static/
│   │   ├── css/ & js/         # Estilos y comportamiento cliente
│   │   └── uploads/covers/    # Almacenamiento local de portadas extraídas
│   └── templates/             # Vistas HTML (Base y Macros)
├── database/                  # [Ruta Externa] Base de datos SQLite (library.db)
├── Iniciar_Biblioteca.bat     # Lanzador principal silencioso
├── launcher.py                # Script de inicio en segundo plano
├── requirements.txt           # Dependencias de Python
└── run.py                     # Script de desarrollo con terminal
```

## 🛡️ Privacidad y Seguridad

Este proyecto fue construido bajo la premisa absoluta de **privacidad por diseño**:

- **Cero Telemetría Oculta:** Sin scripts de seguimiento ni analíticas integradas.
- **100% Local:** Tus datos, metadatos y reseñas se almacenan exclusivamente en tu máquina. Las interacciones con APIs externas (OpenLibrary, Google Books) ocurren **únicamente** cuando decides de manera manual y activa buscar un ISBN para autocompletar un libro, preservando el aislamiento del resto de tu colección.
- **Portabilidad:** Para realizar copias de seguridad de tu biblioteca completa, simplemente copia el archivo `database/library.db` y la carpeta `app/static/uploads/covers/`.

---

<div align="center">
  <i>Construido con simplicidad y rigor para los amantes de los libros.</i>
</div>
