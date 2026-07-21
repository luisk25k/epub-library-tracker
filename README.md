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
- **🗃️ CRUD Completo:** Crea, lee, actualiza y elimina registros literarios con un enfoque riguroso, incluyendo campos profesionales como el nombre del `Traductor` y el `Formato`.
- **📊 Estado de Lectura:** Clasifica fácilmente tu colección visualmente con estados de lectura: *No leído, Leyendo, Leído*.
- **📝 Editor de Reseñas Markdown:** Soporte nativo de Markdown para escribir reseñas extensas, análisis crítico y notas filológicas, renderizadas dinámicamente con una vista previa de doble panel.
- **🎨 Interfaz Moderna y Oscura:** Un diseño UI/UX limpio y minimalista optimizado mediante TailwindCSS en modo oscuro, garantizando la comodidad visual.
- **🔍 Búsqueda y Ordenación:** Filtra rápidamente tu estantería por estatus de lectura o busca directamente autores y títulos.

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Propósito |
|---|---|---|
| **Backend** | Python 3.10+ / Flask | Servidor web eficiente y minimalista. |
| **Base de Datos** | SQLite 3 | Base de datos portable en un solo archivo. |
| **Frontend** | HTML5, TailwindCSS, Vanilla JS | UI responsiva y rápida sin builds pesados de JS. |
| **ePub Parser** | ebooklib / lxml | Lectura y extracción estructurada de archivos ePub. |
| **Markdown** | marked.js | Renderizado seguro de Markdown en el lado del cliente. |

## 🚀 Instalación y Uso

Asegúrate de contar con **Python 3.10 o superior** instalado en tu sistema. El sistema fue construido para ser fácil de levantar sin necesidad de contenedores.

```bash
# 1. Clonar el repositorio
git clone <tu-repositorio>
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

# 5. Iniciar la aplicación
python run.py
```
> La aplicación estará disponible localmente en tu navegador en: **`http://localhost:5000`**

## 📂 Estructura del Proyecto

El sistema está diseñado de forma modular utilizando el patrón de *Application Factory* de Flask.

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
│   └── templates/             # Vistas HTML5 puras (index, form, detail)
├── database/
│   └── library.db             # Archivo SQLite generado automáticamente en runtime
├── tests/                     # Tests de integración
├── run.py                     # Punto de entrada del servidor
└── requirements.txt           # Dependencias de Python
```

## 🛡️ Privacidad y Seguridad

Este proyecto fue construido bajo la premisa absoluta de **privacidad por diseño**:
- **Cero Telemetría:** Sin seguimiento, sin analíticas integradas.
- **100% Local:** Ningún dato, libro, metadato o reseña abandona tu máquina. La aplicación no hace uso de APIs externas de catalogación (como Goodreads o Google Books).
- **Portabilidad:** Para realizar copias de seguridad de tu biblioteca completa, simplemente copia el archivo `database/library.db` y la carpeta `app/static/uploads/covers/`.

---
<div align="center">
  <i>Construido con simplicidad y rigor para los amantes de los libros.</i>
</div>
