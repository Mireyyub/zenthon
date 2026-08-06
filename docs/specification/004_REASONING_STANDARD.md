# 004 Reasoning Standard

Single path: `ReasoningEngine.reason(query)`

Priority of evidence sources:
1. curriculum / train / eval
2. facts
3. graph
4. memory
5. LLM (optional)

Conflict of high-priority yes/no → `UNKNOWN`.

Every call returns: answer, confidence, evidence, trace_id, source, validation, decision.
