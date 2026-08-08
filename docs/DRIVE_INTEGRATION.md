# Drive Leon.təlim → zenthon inteqrasiyası

**Mənbə:** Google Drive `Leon.təlim` (`1gdeJKwxKvlyIj5RQ8yLXhZjCV-83G5hn`)

## Nə inteqrasiya olundu

| Drive / paket | Zenthon yolu | Qeyd |
|---------------|--------------|------|
| zenthon_v08 RAG | `brain/rag/pipeline.py` | chunk + hybrid retrieve |
| zenthon_v08 conversation | `memory/conversation_manager.py` | multi-turn session |
| zenthon_v09 cache | `brain/llm/cache.py` | LLM response cache |
| zenthon_v10 swarm | `agents/swarm.py` | role-based multi-agent + sintez |
| zenthon_v10 prompts | `prompts/registry.py` | hot-reload templates + metrics |
| Local AGI blackboard | `agents/blackboard.py` | facts / decisions / reflections |
| Local AGI dag_runner | `brain/planning/dag_runner.py` | async topological waves + timeout |
| Local AGI decision_engine | `agents/decision_engine.py` | multi-criteria weighted choose |

## Bilərəkdən kənarda qalanlar

- **LEON-mega-v4** (C# / .NET desktop) — Python zenthon-a birbaşa köçürülmədi.
- **AgilBot / Jarvis / Kimi zip** — ayrı məhsullar; core-a merge edilmədi.
- **LoRA finetune** (torch/peft) — optional; Drive README pipeline izahını saxlayır.
- **async_client (httpx heavy)** — mövcud `brain/llm/client.py` sync yolu əsas qalır; async optional gələcək.

## İstifadə

```python
from brain.rag.pipeline import RAGPipeline
from memory.conversation_manager import ConversationManager
from agents.swarm import AgentSwarm
from agents.blackboard import TaskBlackboard
from agents.decision_engine import DecisionEngine
from brain.planning.dag_runner import DAGRunner, DAGNode
from prompts.registry import prompt_registry, render_prompt
```

## Uyğunluq prinsipi

Drive kodu **əlavə qat**dır; mövcud ReasoningEngine / Curriculum / Security path-ləri əvəz edilmədi.
Async client yoxdursa swarm sync LLM-ə düşür.
DAGRunner və DecisionEngine pure Python + asyncio; əlavə dependency tələb etmir.
