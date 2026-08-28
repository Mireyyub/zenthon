# Leon AI Platform (Zenthon)

**Modul əsaslı, offline-first kognitiv AI** — yaddaş, curriculum, reasoning, agent, təhlükəsiz alətlər, lokal LLM.  
Repo: https://github.com/Mireyyub/zenthon

> **Reallıq:** bu **v0.8.0 Alpha** prototipdir. Production AGI **deyil**.  
> Aşağıda yalnız **kodda mövcud** imkanlar yazılıb. İddia ≠ arzu.

**Sənədlər:**  
[`ARCHITECTURE.md`](ARCHITECTURE.md) · [`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md) · [`docs/GAP_ANALYSIS.md`](docs/GAP_ANALYSIS.md) · [`LEGACY.md`](LEGACY.md) · [`docs/PUBLIC_SURFACE.md`](docs/PUBLIC_SURFACE.md) · [`docs/DESKTOP.md`](docs/DESKTOP.md) · [`docs/PACKAGING.md`](docs/PACKAGING.md) · [`docs/E2E.md`](docs/E2E.md)

---

## İşlək imkanlar (dürüst)

| Sahə | Status |
|------|--------|
| Config + `data/leon/` persist | ✅ |
| FactStore / Graph / Learning / Vector (registry) | ✅ |
| Curriculum volumes + eval | ✅ |
| **Tək yol:** ReasoningEngine (evidence, conflict→UNKNOWN, trace) | ✅ |
| Memory retrieve + validated promotion | ✅ |
| Production agents: `react`, `coding` | ✅ |
| Planner | ✅ |
| LLMProvider (Ollama / Mock) | ✅ |
| FastAPI `/api/v1` (127.0.0.1) | ✅ |
| WebSocket `/ws` (typed events) | ✅ |
| Security allowlist + PathSandbox + audit | ✅ |
| SelfView / SelfImprove / gated SelfMutate | ✅ |
| SQLite durable **tasks** (facts/graph hələ JSON-primary) | ⚠️ qismən |
| React UI client (`ui/` — chat + status) | ⚠️ minimal |
| Process supervisor (Python) | ✅ |
| Tauri shell | ⚠️ yalnız seed |
| Windows PyInstaller/NSIS skriptləri | ⚠️ skript səviyyəsi |
| Full document RAG (PDF→rerank) | ❌ hələ yox |
| Full multimodal / AGI | ❌ |

---

## Sürətli start (dev)

```bash
git clone https://github.com/Mireyyub/zenthon.git
cd zenthon
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

# optional local LLM
# ollama serve && ollama pull llama3.2

python run.py
# → http://127.0.0.1:8000/docs
```

Core yoxlama:

```bash
python run.py --check
python -m interfaces.cli.main_cli health
python scripts/e2e_desktop_smoke.py
```

### FastAPI (default: yalnız localhost)

```bash
# tövsiyə olunan — default host 127.0.0.1
uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000

# LAN yalnız şüurlu seçimlə (təhlükəsizlik riski)
# LEON_API_HOST=0.0.0.0 uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000
```

Env: `LEON_API_HOST` (default `127.0.0.1`), `LEON_API_PORT` (default `8000`).

### CLI nümunələri

```bash
python -m interfaces.cli.main_cli start
python -m interfaces.cli.main_cli reason "Daş mövcuddurmu?"
python -m interfaces.cli.main_cli teach-volume 01
python -m interfaces.cli.main_cli agent react "vaxt neçədir?"
python -m interfaces.cli.main_cli health
python -m interfaces.cli.main_cli self body
```

Mutasiya **default bağlıdır** (`LEON_ALLOW_MUTATE` yox / `false`). Açmaq risklidir.

### GUI (Tkinter — işlək, legacy UI yolu)

```bash
python run.py --gui
# və ya
python -m interfaces.gui.main_gui
python leon_desktop.py   # supervisor + GUI entry
```

### React UI (dev)

```bash
cd ui && npm install && npm run dev
# Vite → http://127.0.0.1:5173  (proxy → /api/v1)
```

Brauzerdə AI məntiqi **yoxdur** — yalnız API klient.

---

## Windows paketləmə (dürüst)

Yalnız **Windows** maşında, skript səviyyəsində:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
# quraşdırıcı üçün NSIS lazımdır:
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Installer
```

- Nəticə: `dist/Zenthon/` və opsional `Zenthon-Setup.exe`  
- Bu **store-grade / imzalı Tauri məhsulu deyil**  
- **Autostart opsionaldır** (NSIS-də seçim); məcburi deyil  
- Ətraflı: [`docs/PACKAGING.md`](docs/PACKAGING.md), [`docs/E2E.md`](docs/E2E.md)

Linux desktop qısayol / autostart (opsional):

```bash
python scripts/install_desktop_linux.py --autostart   # seçimlidir
python scripts/install_desktop_linux.py --remove
```

---

## Canonical cognitive path

```
CLI / GUI / FastAPI /ui
  → BrainOrchestrator → ReasoningEngine
  → Curriculum / Facts / Graph / Memory
  → LLMProvider (optional)
  → Agents + Planner + Security gate
  → SelfView / SelfImprove / SelfMutate (gated)
  → data/leon/
```

`ThinkingBrain` yalnız daxili LLM backend-dir — birbaşa UI/agent yolu deyil.

Hybrid desktop xəritəsi (hədəf vs reallıq): [`ARCHITECTURE_AUDIT.md`](ARCHITECTURE_AUDIT.md).

---

## API (qısa)

| Method | Path |
|--------|------|
| GET | `/api/v1/health` |
| GET | `/api/v1/system/desktop` |
| GET | `/api/v1/system/supervisor` |
| POST | `/api/v1/chat` |
| POST | `/api/v1/reason` |
| GET/POST | `/api/v1/tasks` |
| WS | `/ws` |

Tam siyahı: [`docs/PUBLIC_SURFACE.md`](docs/PUBLIC_SURFACE.md)

---

## Test

```bash
pytest tests/unit/test_security.py tests/unit/test_phase10_supervisor.py -q
python scripts/verify_phases_1_8.py
python scripts/verify_phases_9_12.py
python scripts/e2e_desktop_smoke.py
bash scripts/ci_eval.sh
```

---

## Env (əsas)

| Dəyişən | Default / qeyd |
|---------|----------------|
| `LEON_API_HOST` | `127.0.0.1` |
| `LEON_API_PORT` | `8000` |
| `LEON_DATA_DIR` | `data/leon` |
| `LEON_LLM_MODEL` | Ollama model adı |
| `LEON_OLLAMA_HOST` | local Ollama |
| `LEON_ALLOW_MUTATE` | `false` — default bağlı |

---

## Nə iddia etmirik

- AGI / superintelligence  
- Tam production Windows store məhsulu  
- Real Tauri runtime (hələ seed)  
- Tam PDF/DOCX RAG pipeline  
- Məcburi cloud / internet  

*Leon — düşünən, öyrənən, özünü görən **prototip**.*
