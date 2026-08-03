# Leon AI Platform

**Modul əsaslı, yaddaşlı, agent əsaslı, lokal LLM dəstəkli kognitiv süni intellekt — Leon.**

Repo: https://github.com/Mireyyub/zenthon

---

## Nədir?

**Leon** sadəcə ML train/predict aləti deyil. Üzərində:

- **ThinkingBrain** – perception → memory/knowledge/GraphRAG → reasoning (CoT/ToT/SoT) → reflection → decision
- **Agent sistemi** – coding, research, executor, vision, voice, ReAct, PEV, Reflexion, multi-agent Crew
- **Memory qatları** – working, session, archival, vector, semantic, episodic
- **Knowledge + GraphRAG** – faktlar, qraf, hybrid retrieval
- **Lokal LLM** – Ollama (default), OpenAI / xAI / Groq uyğunluğu
- **ML/DL stack** – sklearn + PyTorch modellər, training, LIME/SHAP, FastAPI

---

## Sürətli start

```bash
git clone https://github.com/Mireyyub/zenthon.git
cd zenthon
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Lokal LLM (tövsiyə)
ollama serve
ollama pull llama3.2

# Platform bootstrap
python zenthon_app.py

# CLI think
python -m interfaces.cli.main_cli think "Leon kimdir?" --mode auto

# API
python -m inference.api.fastapi_app
# POST http://localhost:8000/think

# GUI
python -m interfaces.gui.main_gui
```

---

## Arxitektura

```
USER → Interfaces (CLI / GUI / Web / API)
          ↓
     BrainOrchestrator (Leon)
          ↓
 ┌────────┼────────┐
 Reasoning  Memory  Planner
          ↓
    Decision Engine
          ↓
     Agent Manager → Tools / Models / Knowledge
```

### Əsas paketlər

| Paket | Məzmun |
|-------|--------|
| `core/` | kernel, event_bus, async_event_bus, scheduler, registry, lifecycle, checkpoint |
| `brain/` | ThinkingBrain (Leon), CoT/ToT/SoT, reflection, goals, orchestrator, LLM |
| `memory/` | working, session, archival, vector, semantic, manager |
| `knowledge/` | graph, facts, retrieval, graphrag |
| `agents/` | coding, research, executor, vision, voice, react, pev, reflexion, crew |
| `learning/` | feedback, evaluator, self_learning |
| `evaluation/` | metrics, benchmark, runner |
| `tools/` | registry, filesystem |
| `security/` | permissions, audit, sandbox |
| `models/` | ML + DL + ModelRouter |
| `inference/` | predictors, explainers, FastAPI (`/think`) |
| `interfaces/` | CLI, GUI (Brain tab), Web |

---

## ThinkingBrain (Leon)

```python
from brain import ThinkingBrain

brain = ThinkingBrain(name="Leon", enable_meta=True)
result = brain.think(
    "Lokal RAG necə qurulur?",
    goal="Praktiki plan",
    reasoning_mode="auto",  # cot | tot | sot | auto
)
print(result["conclusion"], result["confidence"], result["reflection"])

# Async
import asyncio
result = asyncio.run(brain.athink("Sual"))
```

### Orchestrator

```python
from brain.orchestrator import BrainOrchestrator

orch = BrainOrchestrator(brain_name="Leon")
orch.set_hitl(lambda r: r.get("confidence", 0) >= 0.4)

r = orch.run(
    "Chatbot planı yaz",
    goal="MVP",
    agent_type="pev",
    use_session=True,
    archive_result=True,
    checkpoint_name="chat",
)
```

### Agentlər

```python
from agents import agent_manager, default_research_crew

a = agent_manager.create("react")
print(agent_manager.run(a.id, "Cari vaxtı al").output)

crew = default_research_crew("RAG")
print(crew.run().final)
```

Tiplər: `coding | research | executor | vision | voice | react | pev | reflexion`

### Ollama

```bash
export ZENTHON_LLM_PROVIDER=ollama   # default
export ZENTHON_LLM_MODEL=llama3.2
```

---

## CLI

```bash
python -m interfaces.cli.main_cli think "Sual" --mode sot --goal "..."
python -m interfaces.cli.main_cli agent coding "Fibonacci yaz"
python -m interfaces.cli.main_cli status
```

## API

```bash
python -m inference.api.fastapi_app
```

| Endpoint | Təsvir |
|----------|--------|
| `POST /think` | Leon kognitiv düşünmə |
| `GET /status` | Brain / memory status |
| `POST /predict` | ML/DL proqnoz |
| `GET /health` | Sağlamlıq |
| `/docs` | Swagger |

## GUI

```bash
python -m interfaces.gui.main_gui
```

Tablar: **Brain** (Leon think + mode + agent), Data, Train, Logs

## Evaluation

```bash
python -m brain.examples.demo_eval
python -c "from evaluation import evaluate_brain; print(evaluate_brain(limit=5))"
```

---

## Async

- `core.async_event_bus`
- `ThinkingBrain.athink()`
- `BrainOrchestrator.arun()`
- FastAPI native async

---

## Demolar

```bash
python zenthon_app.py
python -m brain.examples.demo_think
python -m brain.examples.demo_ollama
python -m brain.examples.demo_agents
python -m brain.examples.demo_deep
python -m brain.examples.demo_eval
```

---

## Testlər

```bash
pytest tests/ -q
pytest tests/unit/test_brain.py -q
```

---

## Lisenziya / Əlaqə

Açıq inkişaf.  
GitHub: [Mireyyub](https://github.com/Mireyyub) · Email: mireyyub@gmail.com

---

*Leon – düşünən, yadda saxlayan, agentlərlə işləyən AI.*
