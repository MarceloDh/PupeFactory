import os
from django.conf import settings

# ==============================================================================
# CONTEXT PROCESSOR: DATOS DEL ESTUDIANTE PARA EL FOOTER
# ==============================================================================
# Cumple con el requerimiento de la pauta de evaluación y checklist técnico:
# Renderizar en todas las vistas HTML base los datos: Nombre, Sección y Año.
# Se obtienen desde variables de entorno o valores por defecto del proyecto.
# ==============================================================================

def footer_context(request):
    """
    Inyecta las variables del alumno en el contexto de todos los templates.
    """
    return {
        'ALUMNO_NOMBRE': getattr(settings, 'ALUMNO_NOMBRE', 'Estudiante Backend'),
        'ALUMNO_SECCION': getattr(settings, 'ALUMNO_SECCION', 'Sección 1'),
        'ALUMNO_ANIO': getattr(settings, 'ALUMNO_ANIO', '2026'),
        'PROYECTO_NOMBRE': 'PupeFactory',
    }
