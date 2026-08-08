# Drive Leon.təlim → zenthon inteqrasiyası

**Mənbə:** Google Drive `Leon.təlim` (`1gdeJKwxKvlyIj5RQ8yLXhZjCV-83G5hn`)

## Nə inteqrasiya olundu (real)

| Drive / paket | Zenthon yolu | Status |
|---------------|--------------|--------|
| zenthon_v08 RAG | `brain/rag/pipeline.py` | ✅ |
| zenthon_v08 conversation | `memory/conversation_manager.py` | ✅ |
| zenthon_v09 cache | `brain/llm/cache.py` | ✅ |
| zenthon_v09 async client | `brain/llm/async_client.py` | ✅ lean, optional |
| zenthon_v10 swarm | `agents/swarm.py` | ✅ |
| zenthon_v10 prompts | `prompts/registry.py` | ✅ |
| Local AGI blackboard | `agents/blackboard.py` | ✅ |
| Local AGI dag_runner | `brain/planning/dag_runner.py` | ✅ |
| Local AGI decision_engine | `agents/decision_engine.py` | ✅ |

## Bilərəkdən kənarda / experimental

- **LEON-mega-v4** (C# / .NET desktop) — Python core-a merge edilmədi.
- **AgilBot / Jarvis / Kimi zip** — ayrı məhsullar.
- **code_sandbox.py** — mövcud `security/sandbox.py` + `tools/registry` ilə əhatə olunur; AST whitelist gələcək enhancement kimi qala bilər.
- **LoRA / finetune** — optional, torch tələb edir; core path-də yoxdur.

## İstifadə

```python
from brain.rag.pipeline import RAGPipeline
from memory.conversation_manager import ConversationManager
from agents.swarm import AgentSwarm
from agents.blackboard import TaskBlackboard
from agents.decision_engine import DecisionEngine
from brain.planning.dag_runner import DAGRunner, DAGNode
from prompts.registry import prompt_registry, render_prompt
from brain.llm.async_client import get_async_client  # optional
```

## Uyğunluq prinsipi

Drive kodu **əlavə qat**dır. Mövcud ReasoningEngine, Curriculum, Security gate və CLI path-ləri əvəz edilmir.
Async client yoxdursa və ya Ollama offline-dursa sistem sync yola düşür.
