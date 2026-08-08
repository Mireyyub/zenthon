# Leon.təlim — tam inteqrasiya hesabatı

## Mənbələr (hamısı açıldı və emal edildi)

| Mənbə | Növ | İnteqrasiya |
|-------|-----|-------------|
| zenthon_v08.zip | Python | RAG, conversation → core |
| zenthon_v09.zip | Python | cache, async_client, pipeline ideas |
| zenthon_v10.zip | Python | swarm, tools/engine, prompts, websocket |
| LEON-mega-v4.zip | **C# /.NET** | Skill registry + Math/Help/Think → **Python rewrite** `agents/skills/` |
| AgilBot_v16.zip | Python multi-engine | Domain math/chemistry → `tools/domain/`; digər engine-lər təhlükəsiz subset |
| jarvis-v3.2.0.zip | Python integration | Test/integration patterns; Leon identity tests referans |
| Kimi_Agent.zip | HTML/JS UI only | UI referans — core-a binary deyil |

## Yeni path-lər

- `agents/skills/` — LEON-mega skill system (Python)
- `agents/local_agi/` — Local AGI agent stack
- `agents/decision_engine.py`, `agents/blackboard.py`
- `brain/planning/dag_runner.py`
- `brain/llm/async_client.py`
- `tools/engine.py` — v10 tool calling engine
- `tools/domain/` — AgilBot domain subset (safe)
- `interfaces/websocket/` — v10 WS soft adapter
- `prompts/registry.py`
- `data/leon/intents.json` — mega intents sample

## Uyğunlaşdırma prinsipi

1. C# kod **yenidən yazıldı** (skill registry, risk tags).
2. AgilBot-un təhlükəli/terminal/crypto engine-ləri core-a dump edilmədi; yalnız təhlükəsiz domain.
3. Kimi yalnız frontend — referans.
4. Mövcud ReasoningEngine / Security / Curriculum **qırılmadı**.

## İstifadə

```python
from agents.skills import get_skill_registry
print(get_skill_registry().run("math", "2+3*4").output)

from tools.engine import get_tool_engine
print(get_tool_engine().call("calc", {"expression": "10/2"}).result)

from tools.domain import periodic_lookup
print(periodic_lookup("O"))
```
