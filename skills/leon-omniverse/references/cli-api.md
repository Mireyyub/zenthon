# Leon CLI and API index

## CLI

python -m interfaces.cli.main_cli <cmd>

- start [--bootstrap] [--volume 01]
- smoke | health | status | info | llm-check
- save | load
- teach <lesson_id> | teach-volume <id> | eval <id>
- reason <q> | think <q> [--agent react]
- retrieve <q> | quarantine [--accept id]
- agent --list | agent react <task>
- plan create|list|show|run|replan
- omniverse status|demo|sync|inject|ask

## FastAPI (interfaces.api.main)

- GET /health /status /volumes
- POST /think /reason /teach

uvicorn interfaces.api.main:app --port 8000
