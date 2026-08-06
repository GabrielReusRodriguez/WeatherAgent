# weather_agent (amd-gaia)

Agente de predicción meteorológica con CLI interactivo. Geocodifica con Nominatim, obtiene datos de Open-Meteo y redacta el informe de texto con Mistral (en el idioma que pida el usuario). Lemonade orquesta las tools y devuelve el texto tal cual.

## Requisitos

- Python ≥ 3.10
- Lemonade accesible en `http://ai.core.lan:8080/api/v1` (o `LEMONADE_BASE_URL`)
- Variable de entorno obligatoria: `MISTRAL_API_KEY`

## Instalación

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[test]"
```

O con pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

## Uso

```bash
export MISTRAL_API_KEY="tu-clave"
# opcional:
# export MISTRAL_MODEL="mistral-small-latest"
python main.py
```

Escribe consultas naturales, por ejemplo:

- `¿Qué tiempo hace mañana en Valencia?`
- `Weather in Berlin this weekend in English`
- `Prévisions pour Paris demain en français`

Salir: `salir`, `exit` o `quit`.

## Tests

Los tests unitarios viven en [`tests/`](tests/) y mockean Nominatim, Open-Meteo y Mistral (no requieren red ni Lemonade).

```bash
source .venv/bin/activate
pip install -e ".[test]"   # si aún no tienes pytest
pytest
```

Cobertura aproximada:

| Archivo | Qué valida |
|---------|------------|
| `test_geocode.py` | resolución de lugar, errores vacíos/404/HTTP |
| `test_weather.py` | códigos WMO, current/daily/hourly sanitizados |
| `test_mistral_report.py` | API key, payload a Mistral, `period` en el prompt |
| `test_agent.py` | registro GAIA, tools, `date_from_today`, tool de informe |

## Configuración

- [`gaia-agent.yaml`](gaia-agent.yaml) — modelo y URL Lemonade
- `LEMONADE_BASE_URL` — URL Lemonade (opcional)
- `MISTRAL_API_KEY` — API key de Mistral (obligatoria para redactar el informe)
- `MISTRAL_MODEL` — modelo Mistral (opcional, default `mistral-small-latest`)

## Flujo del agente

1. `date_from_today` — fecha y weekday (fuente de verdad del calendario)
2. `resolve_place` — Nominatim
3. `get_current_weather` / `get_daily_forecast` / `get_hourly_forecast` — Open-Meteo
4. `draft_weather_report` — Mistral recibe JSON con `place`, `period` y `forecast`
5. La respuesta al usuario es exactamente el campo `report` de Mistral
