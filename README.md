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
