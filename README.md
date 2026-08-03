# Leon AI Platform

**Modul əsaslı kognitiv AI — yaddaş, curriculum, reasoning, agent, lokal LLM.**  
Repo: https://github.com/Mireyyub/zenthon

> Reallıq: bu **v0.x prototipdir**. Production AGI deyil. Aşağıdakılar **kodda olan** imkanlardır.

---

## İşlək imkanlar (Faza 0–8)

| Sahə | Status |
|------|--------|
| Config + `data/leon/` persist | ✅ |
| FactStore / Graph / Learning / Vector disk | ✅ |
| Curriculum Volume 01–02 + eval | ✅ |
| ReasoningEngine (evidence, conflict, trace) | ✅ |
| Memory retrieve + promotion | ✅ |
| Production agents: `react`, `coding` (sandbox) | ✅ |
| Planner (create/run/replan) | ✅ |
| CLI + FastAPI + GUI (Think/Teach/Status) | ✅ |
| Omniverse bridge (stub/live) | ✅ |
| Experimental agents (vision/voice/…) | ⚠️ experimental |
| Full multimodal / AGI | ❌ iddia yoxdur |

---

## Sürətli start

```bash
git clone https://github.com/Mireyyub/zenthon.git
cd zenthon
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# optional local LLM
ollama serve && ollama pull llama3.2

python zenthon_app.py
python -m interfaces.cli.main_cli start
python -m interfaces.cli.main_cli teach-volume 01
python -m interfaces.cli.main_cli reason "Daş mövcuddurmu?"
python -m interfaces.cli.main_cli health
```

### FastAPI

```bash
uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000
# POST /think  GET /status  GET /health  POST /teach
```

### GUI

```bash
python -m interfaces.gui.main_gui
# Tabs: Think | Teach | Status
```

---

## Arxitektura (qısa)

```
CLI / GUI / FastAPI
        ↓
BrainOrchestrator → ReasoningEngine
        ↓
Memory (working→promote) + FactStore + Graph + Curriculum
        ↓
Agents (react, coding) + Planner + Tools (sandbox)
        ↓
integrations/omniverse (optional)
```

---

## Omniverse

Leon NVIDIA Omniverse ilə **soft bridge** üzərindən işləyir:

- Kit / `pxr` yoxdursa → **stub scene** (demo obyektlər)
- Varsa → stage-dən prim sync

```python
from integrations.omniverse import OmniverseBridge

ov = OmniverseBridge()
print(ov.status())
ov.load_stub_demo_scene()          # Kit olmadan
# ov.sync_from_stage()             # Kit içində
ov.inject_scene_facts()
print(ov.ask_leon("Səhnədə hansı obyektlər var?"))
```

```bash
python -m interfaces.cli.main_cli omniverse status
python -m interfaces.cli.main_cli omniverse demo
python -m interfaces.cli.main_cli omniverse ask "Səhnədə neçə obyekt var?"
```

---

## CLI (əsas)

```bash
python -m interfaces.cli.main_cli start [--bootstrap]
python -m interfaces.cli.main_cli reason "..."
python -m interfaces.cli.main_cli teach-volume 01
python -m interfaces.cli.main_cli eval 01
python -m interfaces.cli.main_cli retrieve "alma"
python -m interfaces.cli.main_cli agent --list
python -m interfaces.cli.main_cli agent react "vaxt neçədir?"
python -m interfaces.cli.main_cli plan create --goal "öyrən" --curriculum 01
python -m interfaces.cli.main_cli health
python -m interfaces.cli.main_cli smoke
```

Env: `LEON_DATA_DIR`, `LEON_LLM_MODEL`, `LEON_OLLAMA_HOST`, `LEON_EMBED_MODEL`

---

## Test / CI

```bash
pytest tests/unit/test_facts_graph_learning.py tests/integration/test_cognitive_persist.py -q
bash scripts/ci_eval.sh
```

---

## Qeyd

- ML (`models/`) cognitive path-dən **ayrı** optional qatdır.
- Experimental agentlər: bax `agents/EXPERIMENTAL.md`.
- README iddiaları kodla uyğun saxlanılır; şişirdilmir.

GitHub: [Mireyyub](https://github.com/Mireyyub) · mireyyub@gmail.com

*Leon – düşünən, öyrənən, yadda saxlayan prototip.*
