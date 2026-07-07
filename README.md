# app_seguimiento_moodle

App en Streamlit para dar seguimiento a estudiantes en plataforma **Moodle** vía REST API. Genera un reporte Excel con el progreso de cada estudiante por curso.

## Funcionalidades

- **Carga de CSV**: formato `nombre;apellido;email;dni` (separado por punto y coma)
- **Búsqueda en Moodle**: por DNI (username → idnumber), fallback por nombre
- **Procesamiento paralelo**: hasta 3 estudiantes simultáneos (~40s para 15 estudiantes)
- **Reporte Excel** con estilos:
  - Hoja 1 — Reporte detallado: DNI, Nombre, Curso, Progreso, Último módulo, Fecha
  - Hoja 2 — Resumen por curso: Inscriptos, Sin inicio, % En curso, Completos
  - Fuente Montserrat, encabezado gris, filas alternadas, celdas fusionadas
- **Resumen estadístico** en la UI con métricas y tabla por curso

## Archivos del proyecto

| Archivo | Propósito |
|---|---|
| `app.py` | Interfaz Streamlit |
| `moodle_client.py` | Cliente API Moodle |
| `.env` | Configuración (URL + token) — **no se sube a git** |
| `.env.example` | Template de configuración |
| `requirements.txt` | Dependencias |
| `.gitignore` | Ignora `.env`, `__pycache__` |
| `documentacion/` | Archivos de ejemplo del reporte de salida |

## Consideraciones de diseño

### Repositorio público
El repositorio es **público** porque Streamlit Community Cloud (plan gratuito) solo permite **una app privada por workspace**. Al hacerlo público, se pueden desplegar apps ilimitadas. El código subido no contiene datos sensibles (ver abajo).

### Privacidad de datos personales
- Los datos de estudiantes **nunca se almacenan** en el servidor de Streamlit ni en GitHub
- El archivo CSV se carga en **memoria temporal**, se procesa y se descarta al cerrar la app
- Los reportes generados se descargan directamente al navegador del usuario, sin persistencia
- El archivo `documentacion/` (con datos de ejemplo) se eliminó del repositorio y se agregó a `.gitignore`

### Seguridad de credenciales
- La URL y token de Moodle se configuran en el archivo `.env` **local**, que está en `.gitignore` y nunca se sube a GitHub
- En producción (Streamlit Cloud), se configuran via **Secrets** del dashboard, cifrados por la plataforma
- No hay credenciales hardcodeadas en el código fuente

## Cómo usar

1. Subí un archivo CSV con formato `nombre;apellido;email;dni`
2. Apretá **Ejecutar seguimiento**
3. Descargá el Excel con el reporte

## Despliegue

- **GitHub**: [Sam-2026-code/app_seguimiento_moodle](https://github.com/Sam-2026-code/app_seguimiento_moodle)
- **Streamlit Cloud**: [appseguimientomoodle-nqkatxi8rueleackfnhg6y.streamlit.app](https://appseguimientomoodle-nqkatxi8rueleackfnhg6y.streamlit.app/)

## Compartir la app

Cualquier persona con la URL puede usar la app desde el navegador, sin necesidad de cuenta:

```
https://appseguimientomoodle-nqkatxi8rueleackfnhg6y.streamlit.app/
```

### Límites del plan gratuito (Streamlit Community Cloud)

| Aspecto | Límite |
|---|---|
| Usuarios simultáneos | Hasta **3** (el 4to espera a que se libere un lugar) |
| Reactivación | La app se duerme tras inactividad; se reactiva sola al primer acceso (~15s) |
| Datos subidos | Solo existen en memoria mientras la app está abierta |
| Reportes generados | Se descargan al navegador, no quedan almacenados en el servidor |

Si el equipo necesita más de 3 usuarios simultáneos, habría que upgradear a **Streamlit Teams** (USD $349/mes aprox).

## Desarrollo local

### Prerrequisitos
- Python 3.10+
- pip

### Instalación

```bash
git clone https://github.com/Sam-2026-code/app_seguimiento_moodle.git
cd app_seguimiento_moodle
pip install -r requirements.txt
```

### Configuración

Crear un archivo `.env` en la raíz del proyecto:

```
MOODLE_URL=https://escueladesig.com.ar/clases
MOODLE_TOKEN=tu-token-del-webservice
```

### Ejecutar

```bash
streamlit run app.py
```

## Estructura del código

### `app.py`
Interfaz de usuario Streamlit. Maneja: subida de archivos, barra de progreso, métricas, tabla de resultados y descarga del Excel con estilos.

### `moodle_client.py`
Clase `MoodleClient` con los siguientes métodos que consultan la API REST de Moodle:

| Método | API de Moodle | Descripción |
|---|---|---|
| `find_user_by_dni()` | `core_user_get_users_by_field` | Busca estudiante por DNI (username → idnumber) |
| `find_user_by_name()` | `core_user_get_users` | Busca por nombre + apellido |
| `get_user_courses()` | `core_enrol_get_users_courses` | Obtiene los cursos del estudiante |
| `get_course_progress()` | `core_completion_get_activities_completion_status` | Calcula progreso, último módulo y fecha |
| `_get_course_sections()` | `core_course_get_contents` | Obtiene nombres de las secciones del curso |
| `_get_course_lastaccess()` | `core_user_get_course_user_profiles` | Obtiene la fecha del último acceso |

El método `process_csv()` es un generator que procesa el DataFrame: filtra filas vacías, busca cada estudiante en Moodle (en paralelo, hasta 3 simultáneos) y yield actualizaciones de progreso para la UI.

### Dependencias

| Librería | Uso |
|---|---|
| `streamlit` | Framework de la interfaz web |
| `requests` | Llamadas HTTP a la API REST de Moodle |
| `pandas` | Manipulación de DataFrames (CSV de entrada y Excel de salida) |
| `openpyxl` | Generación y estilo del archivo Excel (.xlsx) |
| `python-dotenv` | Lectura del archivo `.env` en entorno local |

## Formato del CSV de entrada

Archivo de texto con separador `;` (punto y coma), encoding **latin1** (ISO-8859-1), con encabezado:

```csv
nombre;apellido;email;dni
Silvia;Alaniz;salaniz@mecon.gov.ar;31138583
Marcos;Fernandez;marcfernan@mecon.gov.ar;33266738
```

Las columnas requeridas son: `nombre`, `apellido`, `email`, `dni`. Las filas vacías se omiten automáticamente.

## Troubleshooting

| Problema | Causa probable | Solución |
|---|---|---|
| "No se encontró configuración de Moodle" | Secrets no configurados en Streamlit Cloud | Settings > Secrets > pegar `MOODLE_URL` y `MOODLE_TOKEN` |
| App se queda cargando sin progreso | Timeout o error de conexión al servidor Moodle | Verificar que la URL y token sean correctos; probar conectividad manual |
| Error de encoding en CSV | El archivo no está en latin1 | Guardar el CSV con codificación ISO-8859-1 (ANSI) |
| El repo de GitHub no aparece en Streamlit | Streamlit vinculado a otra cuenta de GitHub | Asegurar que la sesión de Streamlit use la misma cuenta de GitHub que el repo |
