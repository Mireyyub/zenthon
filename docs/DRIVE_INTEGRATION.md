# Drive Leon.təlim → zenthon — tam inventar

**Mənbə folder:** Google Drive `Leon.təlim`  
**ID:** `1gdeJKwxKvlyIj5RQ8yLXhZjCV-83G5hn`

## 1. Əsas paketlərə inteqrasiya olunanlar (adapted, production path)

| Drive faylı | Zenthon yolu | Qeyd |
|-------------|--------------|------|
| blackboard.py | `agents/blackboard.py` | TaskBlackboard + facts/decisions/reflections |
| decision_engine.py | `agents/decision_engine.py` | multi-criteria weighted |
| dag_runner.py | `brain/planning/dag_runner.py` | async topological waves |
| (v10) prompts/registry | `prompts/registry.py` | versioned templates + metrics |
| (v09) async_client | `brain/llm/async_client.py` | lean optional async Ollama |
| (v08) RAG pipeline | `brain/rag/pipeline.py` | chunk + hybrid retrieve |
| (v08) conversation | `memory/conversation_manager.py` | multi-turn |
| (v09) cache | `brain/llm/cache.py` | LLM response cache |
| (v10) swarm | `agents/swarm.py` | role-based multi-agent |
| base_agent.py | `agents/local_agi/base_agent.py` | circuit-breaker BaseAgent |

## 2. Local AGI agent stack (agents/local_agi/)

Drive agentləri ayrı namespace-də saxlanılır ki, mövcud `agents/react_agent`, `coding_agent` və s. ilə conflict olmasın.

| Drive | Status |
|-------|--------|
| base_agent.py | ✅ `agents/local_agi/base_agent.py` |
| planner_agent.py | 🔄 növbəti — BaseAgent subclass |
| reasoning_agent.py | 🔄 növbəti |
| execution_agent.py | 🔄 növbəti |
| critic_agent.py | 🔄 növbəti |
| memory_agent.py | 🔄 növbəti |
| orchestrator.py / orchestrator_v2.py | 🔄 növbəti — mövcud brain/orchestrator ilə merge |
| self_improvement.py | 🔄 növbəti — mövcud brain/self_improve ilə müqayisə |

## 3. Tools / memory / infra (Drive → uyğun paket)

| Drive | Hədəf / status |
|-------|----------------|
| code_sandbox.py | mövcud `security/sandbox.py` + AST whitelist enhancement plan |
| browser_tool.py | `tools/` experimental |
| file_tool.py | mövcud `tools/safe_fs.py` / `tools/filesystem.py` |
| episodic.py / long_term.py / short_term.py | mövcud `brain/memory/*` + `memory/*` ilə uyğunlaşdırma |
| session_manager.py | `memory/session.py` mövcud |
| ollama_client.py | mövcud `brain/llm/client.py` |
| prompt_templates.py | `prompts/` + registry |
| ws_server.py | `interfaces/` experimental |
| api_extensions.py | `interfaces/api/` |
| doctor.py / health_cli.py | `interfaces/cli/` / health |
| trace_logger.py | mövcud traces + audit |
| capabilities.py | registry / status |
| dataset_prep.py / finetune.py / export_gguf.py | `training/` experimental (torch optional) |
| config.py / config_training.py | mövcud `core/config.py` |
| system.py / main.py / main_v2.py / start.py | entrypoint referans — `zenthon_app.py` əsasdır |
| chat.py / chat.html | GUI/web referans |
| run_tests.py / test_integration.py | tests/ referans |
| usage.py | docs |

## 4. Bilərəkdən core-a MERGE EDİLMƏYƏN (səbəb ilə)

| Fayl / paket | Səbəb |
|--------------|-------|
| **LEON-mega-v4.zip** | C# / .NET desktop — Python zenthon core deyil |
| **AgilBot_v16.zip** | Ayrı məhsul |
| **jarvis-v3.2.0.zip** | Ayrı məhsul |
| **Kimi_Agent_*.zip** | Ayrı məhsul |
| local_agi_system_design.html | Dizayn sənədi — docs-a kopyalana bilər |

Bu zip-lər Drive-da qalır; zenthon core-a binary dump edilmir.

## 5. Prinsip

- Drive kodu **əlavə qat**dır.
- Mövcud ReasoningEngine, Curriculum, Security gate, CLI **əvəz edilmir**.
- Local AGI agentləri `agents/local_agi/` namespace-indədir.
- Experimental / heavy (finetune, faiss, websocket) soft-import + honest stub.

## 6. İstifadə

```python
from agents.blackboard import TaskBlackboard
from agents.decision_engine import DecisionEngine
from agents.local_agi import BaseAgent, AgentResult
from brain.planning.dag_runner import DAGRunner, DAGNode
from prompts.registry import prompt_registry, render_prompt
from brain.llm.async_client import get_async_client
```
