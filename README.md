# Termómetro Cultural – Social Sentiment Monitoring System

Sistema de monitoreo de sentimiento en redes sociales para el municipio de **Tuluá** (Valle del Cauca, Colombia). Ingiere publicaciones de Facebook, Instagram, X (Twitter) y noticias; las procesa con LLMs para clasificar sentimiento y temas; almacena resultados en PostgreSQL y expone datos vía API para dashboards e informes.

## Arquitectura

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Scheduler  │───▶│  Ingestion   │───▶│  Processing │───▶│   Storage   │
│  (Celery/   │    │  (Scrapers)  │    │  (LLM/NLP)   │    │ (PostgreSQL)│
│   Cron)     │    └─────────────┘    └─────────────┘    └──────┬──────┘
└─────────────┘           │                    │                  │
                           │                    │                  ▼
                           │                    │           ┌─────────────┐
                           │                    │           │    API      │
                           │                    │           │  (FastAPI)  │
                           │                    ▼           └──────┬──────┘
                           │             ┌─────────────┐             │
                           └────────────▶│  Analysis   │◀────────────┘
                                          │ (Aggregates)│
                                          └─────────────┘
```

### Capas

| Capa | Descripción |
|------|-------------|
| **ingestion** | Scrapers (Playwright/BeautifulSoup) para Facebook, Instagram, X, noticias. Salida normalizada en JSON. |
| **processing** | Pipeline NLP: limpieza de texto, clasificación de sentimiento y temas con OpenAI/Grok. |
| **storage** | PostgreSQL + SQLAlchemy. Modelos: posts, comentarios, sentimientos, temas. Redis opcional para cola. |
| **api** | FastAPI: endpoints para dashboards, reportes, filtros por fecha/fuente/sentimiento. |
| **analysis** | Agregaciones y métricas (tendencias, distribución de sentimiento, temas más mencionados). |
| **scheduler** | Orquestación de tareas: ejecución periódica de scrapers y pipeline de procesamiento. |

## Stack tecnológico

- **Python 3.11+**
- **FastAPI** – API REST
- **PostgreSQL** – Base de datos principal
- **SQLAlchemy 2.0** – ORM y migraciones
- **Playwright** – Scraping de páginas dinámicas
- **BeautifulSoup** – Páginas estáticas
- **OpenAI / Grok** – Clasificación de sentimiento y temas
- **Redis** (opcional) – Cola de tareas / caché
- **Docker** – Contenedores y orquestación

## Estructura del proyecto

Ver [ARCHITECTURE.md](docs/ARCHITECTURE.md) para la descripción detallada de cada carpeta.

## Inicio rápido

1. **Variables de entorno**

   ```bash
   cp .env.example .env
   # Editar .env con claves y URLs
   ```

2. **Con Docker**

   ```bash
   docker-compose up -d
   ```

   - API: http://localhost:8000  
   - Docs: http://localhost:8000/docs  

3. **Sin Docker (desarrollo)**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   playwright install chromium
   uvicorn app.api.main:app --reload
   ```

## Uso del módulo de scraping

```python
from app.ingestion.scrapers import FacebookScraper, NewsScraper

scraper = FacebookScraper(proxy_rotation=True)
items = await scraper.scrape(url="https://facebook.com/...")
# items: list[dict] con schema normalizado (source, platform, text, date, url, metadata)
```

## Licencia

Uso interno – Municipio de Tuluá.
