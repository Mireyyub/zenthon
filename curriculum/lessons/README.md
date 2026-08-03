# LEON Curriculum Lessons

Hər dərs `NNNNNN_name.md` formatındadır.

## Struktur

- Lesson ID / Name / Version
- GOAL
- CONCEPT N
- RULES
- QUESTIONS
- SELF TEST

## İstifadə

```python
from curriculum import CurriculumEngine

eng = CurriculumEngine()
print(eng.list_available())
report = eng.teach("000001")
print(report)
```

```bash
python -m interfaces.cli.main_cli teach 000001
python -m interfaces.cli.main_cli lessons
```
