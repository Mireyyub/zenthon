# Leon AI Platform

**Modul əsaslı kognitiv AI — yaddaş, curriculum, reasoning, agent, özünü-təkmilləşdirmə, lokal LLM.**  
Repo: https://github.com/Mireyyub/zenthon

> Reallıq: bu **v0.7 prototipdir**. Production AGI deyil. Aşağıdakılar **kodda olan** imkanlardır.

**Arxitektura:** [`ARCHITECTURE.md`](ARCHITECTURE.md) · Legacy: [`LEGACY.md`](LEGACY.md)

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
| SelfView (öz kodunu görür) | ✅ |
| SelfImprove + green-gate codegen | ✅ |
| Controlled self-mutate (`LEON_ALLOW_MUTATE`) | ✅ |
| SystemLoop (system status/improve) | ✅ |
| Experimental agents | ⚠️ |
| Full multimodal / AGI | ❌ |

---

## Sürətli start

### VS Code — tək əmr

Reponu VS Code ilə açın və terminalda yalnız aşağıdakı əmri icra edin. İlk çalışmada `.venv` avtomatik yaradılır, core asılılıqlar quraşdırılır və API `http://127.0.0.1:8000/docs` ünvanında açılır.

```bash
python run.py
```

VS Code içində alternativ olaraq **Terminal → Run Build Task** seçin və ya `F5` düyməsi ilə **Leon AI: Run local API** konfiqurasiyasını başladın. Core yoxlaması üçün `python run.py --check` istifadə edin.

### Masaüstü tətbiqi və local bridge

`python run.py --desktop` ilk açılışda lokal `.venv` və layihə asılılıqlarını hazırlayır, sonra Zenthon qrafik tətbiqi ilə onun local-only FastAPI bridge xidmətini birlikdə açır. Bridge yalnız `127.0.0.1` / `::1` / `localhost` üzərində dinləyir; GUI bağlandıqda bridge də nizamlı olaraq dayandırılır.

```bash
python run.py --desktop
python scripts/install_desktop_linux.py --autostart
```

`--gui` köhnə uyğunluq aliasıdır və eyni birləşik desktop runtime-ı işə salır. Linux autostart əmri tətbiqi sistem menyusuna **Zenthon AI Platform** kimi əlavə edir və kompüterə daxil olarkən avtomatik başlatmanı aktivləşdirir. Qısayol və autostart qeydlərini silmək üçün `python scripts/install_desktop_linux.py --remove` işlədin.

İlk desktop açılışında Zenthon yerli profil sihirbazını göstərir. Sihirbaz CPU, RAM və CUDA vəziyyətini faktiki olaraq aşkarlayır, resursa uyğun profil/model adı təklif edir, yerli data qovluğunu seçməyə imkan verir və səs funksiyaları ilə məhdud hadisə tarixçəsi üçün ayrıca istifadəçi seçimi saxlayır. Bu ekran model yükləmir, Ollama servisini başlatmır və mikrofonu açmır. Model vəziyyəti yalnız `localhost`/loopback Ollama üçün qısa yoxlanılır; servis yoxdursa deterministik fallback açıq qalır.

Command Center-dakı **Operations** bölməsi məhdud, redaktə edilmiş yerli event feed, faktiki scheduler tapşırığı, aktiv agent və vektor yaddaşı xülasəsini göstərir. **Local Setup** bölməsi isə qeyd edilmiş profil, hardware və model sağlamlıq vəziyyətini yeniləməyə və sihirbazı yenidən açmağa imkan verir. Xam sorğu, cavab və reasoning məzmunu event feed-də göstərilmir.

### Windows 11 masaüstü paketi

Windows 11-də tətbiqi qrafik masaüstü proqramı kimi açmaq üçün:

```powershell
python run.py --desktop
```

Yayım üçün `.exe` və quraşdırıcı yaratmaq yalnız Windows-da edilir. Əvvəlcə [NSIS](https://nsis.sourceforge.io/) quraşdırın, sonra PowerShell-dən aşağıdakı əmri icra edin:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1 -Installer
```

Nəticə `dist\Zenthon-Setup.exe` olur. Quraşdırıcı Start Menu və Desktop qısayolları yaradır, həmçinin istifadəçi Windows-a daxil olduqda tətbiqi avtomatik başladır. Silmək üçün Windows **Installed apps** bölməsindən `Zenthon AI Platform`-ı seçin.

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
python -m interfaces.cli.main_cli system status
python -m interfaces.cli.main_cli health
```

### Ayrı FastAPI (inkişaf / inteqrasiya)

```bash
uvicorn interfaces.api.main:app --host 127.0.0.1 --port 8000
```

`/native-core/events` yalnız loopback client-ları qəbul edir və məhdud, redaktə edilmiş əməliyyat hadisələrini qaytarır; xam sorğu, cavab və reasoning məzmunu bu feed-ə yazılmır.

### GUI

```bash
python -m interfaces.desktop.runtime
```

Birbaşa `python -m interfaces.gui.main_gui` yalnız legacy GUI rejimidir və companion API-ni başlatmır.

---

## Canonical path

```
CLI / GUI / FastAPI
  → BrainOrchestrator → ReasoningEngine
  → Curriculum / Facts / Graph / Memory
  → Agents + Planner + Security
  → SelfView / SelfImprove / SelfMutate (gated)
  → data/leon/
```

`ThinkingBrain` yalnız LLM backend kimi daxili istifadə olunur.

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

# özünü görmə
python -m interfaces.cli.main_cli self body
python -m interfaces.cli.main_cli self read --path brain/reasoning/engine.py --start 1

# özünü təkmilləşdirmə
python -m interfaces.cli.main_cli improve auto --volumes 01,02 --rounds 3
python -m interfaces.cli.main_cli system improve --rounds 2
python -m interfaces.cli.main_cli system smoke

# mutasiya (diqqət: LEON_ALLOW_MUTATE=1)
export LEON_ALLOW_MUTATE=1
python -m interfaces.cli.main_cli mutate status
python -m interfaces.cli.main_cli mutate write --goal "helper" --create --apply
```

Env: `LEON_DATA_DIR`, `LEON_LLM_MODEL`, `LEON_OLLAMA_HOST`, `LEON_EMBED_MODEL`, `LEON_ALLOW_MUTATE`

Əlavə local runtime parametrləri: `LEON_EVENT_PERSIST=0|1` və `LEON_EVENT_HISTORY_MAX=10..5000`. Etibarsız LLM timeout/temperature/token və event həddi dəyərləri təhlükəsiz sərhədlərə normallaşdırılır.

İsteğe bağlı ML və vision paketləri ayrıca profil olaraq qurulur; profil seçimi və səbəbləri üçün [`docs/DEPENDENCY_PROFILES.md`](docs/DEPENDENCY_PROFILES.md) sənədinə baxın.

---

## Test

```bash
pytest tests/unit/test_facts_graph_learning.py tests/unit/test_security.py tests/unit/test_self_view.py -q
python run.py --check
python scripts/verify_phases_1_8.py
bash scripts/ci_eval.sh
```

GitHub: [Mireyyub](https://github.com/Mireyyub)

*Leon – düşünən, öyrənən, özünü görən prototip.*
