# 001 Learning Standard

Pipeline: `observe → normalize → conflict-check → validate → commit → index`

## Status values
- `pending` – unverified (working memory only)
- `validated` – promote to FactStore + vector/semantic
- `rejected` / quarantine

## Thresholds (LearningEngine)
- validate if confidence ≥ 0.75
- reject if confidence ≤ 0.25

## API
```python
LearningEngine.observe(content, source, confidence) -> LearningRecord
LearningEngine.validate_record(id, accept=True)
LearningEngine.promote path is internal via _commit
```
