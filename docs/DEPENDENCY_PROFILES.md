# Zenthon Dependency Profiles

Zenthon starts from a **local-first core profile**. Heavy legacy ML and optional vision packages are deliberately separate so a Windows 11 machine can open the Command Center and use deterministic reasoning without first downloading large framework wheels.

| Profile | Command | Includes | Intended use |
|---|---|---|---|
| Core | `python run.py --desktop` | FastAPI, local persistence, NumPy/Pandas, system telemetry | Default Command Center, local API, reasoning fallback |
| ML | `python run.py --desktop --with-ml` | Torch, scikit-learn, SciPy, visualisation, legacy web dependency | Local ML/training and legacy model modules |
| Vision | `python run.py --desktop --with-vision` | Pillow and OpenCV | Local image metadata and image operations |
| Full | `python run.py --desktop --with-all` | Core, ML and Vision | Developer or release-validation environment |

The optional profiles do **not** install or download a local LLM. The first-run wizard only records the desired Ollama model name and performs a short loopback health check. Use `python run.py --prepare-ollama` only when the operator explicitly wants the locally installed Ollama CLI to prepare its service.

> The Windows release build intentionally uses `requirements-full.txt`, because a packaged release must contain the capabilities advertised by its installed optional modules. The build runs GUI-free core and loopback bridge smoke checks before producing the installer.
