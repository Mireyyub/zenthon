# Leon AI Platform

**Modul əsaslı kognitiv AI — yaddaş, curriculum, reasoning, agent, lokal LLM.**  
Repo: https://github.com/Mireyyub/zenthon

> Reallıq: bu **v0.x prototipdir**. Production AGI deyil. Aşağıdakılar **kodda olan** imkanlardır.

**Arxitektura:** bax [`ARCHITECTURE.md`](ARCHITECTURE.md) · Legacy: [`LEGACY.md`](LEGACY.md)

---

## İşlək imkanlar

| Sahə | Status |
|------|--------|
| Config + `data/leon/` persist | ✅ |
| FactStore / Graph / Learning / Vector (registry) | ✅ |
| Curriculum Volume 01–02 + eval | ✅ |
| **Tək yol:** ReasoningEngine (evidence, conflict, trace) | ✅ |
| Memory retrieve + promotion | ✅ |
| Production agents: `react`, `coding` | ✅ |
| Planner | ✅ |
| CLI + FastAPI + GUI | ✅ |
| Omniverse bridge (stub/live) | ✅ |
| Security allowlist + sandbox | ✅ |
| Experimental agents | ⚠️ |
| Full multimodal / AGI | ❌ |

---

## Sürətli start

```bash
git clone https://github.com/Mireyyub/zenthon.git
cd zenthon
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# optional
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
```

### GUI

```bash
python -m interfaces.gui.main_gui
```

---

## Canonical path

```
CLI / GUI / FastAPI
  → BrainOrchestrator → ReasoningEngine
  → Curriculum / Facts / Graph / Memory
  → Agents (react, coding) + Planner + Security
  → data/leon/
```

`ThinkingBrain` yalnız LLM backend kimi daxili istifadə olunur — ictimai think API deyil.

---

## CLI

```bash
python -m interfaces.cli.main_cli start [--bootstrap]
python -m interfaces.cli.main_cli reason "..."
python -m interfaces.cli.main_cli teach-volume 01
python -m interfaces.cli.main_cli eval 01
python -m interfaces.cli.main_cli agent react "vaxt neçədir?"
python -m interfaces.cli.main_cli plan create --goal "öyrən" --curriculum 01
python -m interfaces.cli.main_cli omniverse demo
python -m interfaces.cli.main_cli health
```

Env: `LEON_DATA_DIR`, `LEON_LLM_MODEL`, `LEON_OLLAMA_HOST`, `LEON_EMBED_MODEL`

---

## Test

```bash
pytest tests/unit/test_facts_graph_learning.py tests/unit/test_security.py -q
python scripts/verify_phases_1_8.py
bash scripts/ci_eval.sh
```

GitHub: [Mireyyub](https://github.com/Mireyyub) · mireyyub@gmail.com

*Leon – düşünən, öyrənən, yadda saxlayan prototip.*
