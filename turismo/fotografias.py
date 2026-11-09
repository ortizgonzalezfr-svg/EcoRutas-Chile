import json
from functools import lru_cache
from pathlib import Path
from django.utils.html import strip_tags

CARPETA_FOTOGRAFIAS = Path(__file__).resolve().parent / 'datos' / 'fotografias'

@lru_cache(maxsize=1)
def creditos_fotografias():
    ruta = CARPETA_FOTOGRAFIAS.parent / 'creditos_fotografias.json'
    registros = json.loads(ruta.read_text(encoding='utf-8'))
    return {registro['codigo']: {
        'autor': strip_tags(registro['Artist']),
        'fuente': registro['fuente'],
        'licencia': registro['LicenseShortName'],
        'enlace_licencia': registro['LicenseUrl'],
    } for registro in registros}
