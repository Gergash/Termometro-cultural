# Arquitectura – Termómetro Cultural

## Estructura de carpetas

```
Termometro cultural/
├── app/
│   ├── ingestion/          # Ingesta desde redes y noticias
│   │   ├── scrapers/       # Módulo de scraping (BaseScraper + implementaciones)
│   │   ├── tasks.py        # Tareas de ingesta (orquestación)
│   │   └── schemas.py      # Esquemas de salida normalizados
│   ├── processing/         # Pipeline NLP
│   │   ├── pipeline.py     # Orquestador del pipeline
│   │   ├── sentiment.py   # Clasificación de sentimiento (LLM)
│   │   ├── topics.py       # Extracción/clasificación de temas
│   │   └── normalizer.py  # Limpieza de texto
│   ├── storage/            # Persistencia
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── repositories/   # Acceso a datos
│   │   └── database.py     # Conexión y sesión
│   ├── api/                 # Capa REST
│   │   ├── main.py         # App FastAPI
│   │   ├── routes/         # Endpoints por dominio
│   │   └── dependencies.py # Inyección de dependencias
│   ├── analysis/           # Agregaciones y métricas
│   │   ├── aggregates.py  # Tendencias, distribuciones
│   │   └── reports.py     # Generación de reportes
│   ├── scheduler/          # Planificación
│   │   └── jobs.py        # Tareas programadas (scrape + process)
│   └── config.py           # Configuración centralizada
├── tests/
├── scripts/                 # Utilidades y one-off
├── requirements.txt
├── .env.example
├── docker-compose.yml
└── README.md
```

## Descripción de capas

### ingestion

- **Propósito:** Obtener datos crudos de redes sociales y noticias en formato normalizado.
- **scrapers/:** Interfaz `BaseScraper` e implementaciones por plataforma (Facebook, Instagram, Twitter, Noticias). Playwright para contenido dinámico, BeautifulSoup para estático; soporte a rotación de proxies.
- **tasks.py:** Lanza scrapers por fuente y persiste resultados en cola o en storage.
- **schemas.py:** Contrato de salida: `source`, `platform`, `text`, `date`, `url`, `metadata`.

### processing

- **Propósito:** Limpiar texto, clasificar sentimiento y temas con LLM (OpenAI o Grok).
- **pipeline.py:** Secuencia: normalizer → sentiment → topics; entrada/salida en JSON.
- **sentiment.py / topics.py:** Llamadas a API del LLM y parseo de respuestas.
- **normalizer.py:** Lowercase, eliminación de URLs/emojis opcional, truncado.

### storage

- **Propósito:** Persistir posts, comentarios, resultados de sentimiento y temas.
- **models/:** Tablas PostgreSQL (posts, comments, sentiment_scores, topics, etc.).
- **repositories/:** Capa de acceso (CRUD y consultas por filtros).
- **database.py:** Engine, sesión, lifecycle de FastAPI.

### api

- **Propósito:** Exponer datos para dashboards y reportes.
- **main.py:** App FastAPI, CORS, routers.
- **routes/:** Ej.: `/posts`, `/sentiment`, `/topics`, `/analysis/trends`.
- **dependencies.py:** DB session, servicios inyectados.

### analysis

- **Propósito:** Agregaciones para dashboards (tendencias, distribuciones, temas más frecuentes).
- **aggregates.py:** Consultas agregadas por fecha, fuente, sentimiento.
- **reports.py:** Generación de reportes (resúmenes, export).

### scheduler

- **Propósito:** Ejecutar ingesta y procesamiento de forma periódica.
- **jobs.py:** Definición de tareas (ej. cada N horas: scrape → process). Integrable con Celery, Cron o APScheduler.

## Flujo de datos

1. **Scheduler** dispara tareas de ingesta (por fuente o todas).
2. **Ingestion** ejecuta scrapers; salida en JSON normalizado.
3. Opcional: mensajes a **Redis** para desacoplar.
4. **Processing** toma items de la cola o de la DB; ejecuta pipeline NLP; escribe resultados en **storage**.
5. **API** y **Analysis** leen desde **storage** para servir dashboards y reportes.

## Buenas prácticas aplicadas

- Separación clara por capas (ingestion, processing, storage, api, analysis, scheduler).
- Esquema de scraping normalizado y reutilizable.
- Configuración por entorno (.env) y validación con Pydantic en `config.py`.
- Contenedores Docker para API, DB, Redis y workers (opcional).
- Código de scraping con interfaz base, fácil de extender a nuevas fuentes.
