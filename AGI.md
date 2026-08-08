# Leon və AGI — dürüst xəritə

**Leon AGI deyil.** Bu sənəd marketinq deyil; istiqamət və sərhədlərdir.

## AGI nədir (praktiki)

Geniş mənada AGI: yeni domenlərdə öyrənmək, məqsəd qoymaq, plan qurmaq,
alət istifadə etmək, öz səhvlərini düzəltmək və bilikləri transfer etmək.

## Leon-da olan (v0.8 istiqaməti)

| Bacarıq | Status | Modul |
|---------|--------|--------|
| Structured reason + evidence | ✅ prototip | ReasoningEngine |
| Curriculum learning 01–03 | ✅ | curriculum/ |
| Episodic / vector memory | ✅ | memory/ |
| Tool-using agents (react) | ✅ məhdud | agents/ |
| Self-improve + gated mutate | ✅ | self_improve, self_mutate |
| Body awareness | ✅ | self_view |
| Cognitive cycle PODALR | ✅ | cognitive_cycle |
| Open-world autonomy | ❌ | — |
| Robust multi-domain transfer | ❌ zəif | — |
| Reliable long-horizon planning | ⚠️ | planner |
| Human-level multimodal | ❌ | multimodal local+optional VLM |

## Cognitive Cycle (PODALR)

```
Perceive  → input / image / memory hits
Orient    → retrieve + classify task
Decide    → ReasoningEngine (+ reflection)
Act       → optional agent / tool
Learn     → store outcome if validated
Reflect   → meta quality, next strategy
```

Bu dövrə **ümumi intellekt arxitekturasının** minimal skeletidir —
tək başına AGI yaratmır.

## Növbəti real addımlar (prioritet)

1. Daha dərin curriculum (math, language, social)
2. Transfer eval: vol01 biliklərini vol03-də ölç
3. Long-horizon planner + world state
4. Safer open tool use
5. Human eval suite (not only unit tests)

## Qırmızı xətt

- README/AGI.md-də “AGI-yik” yazılmır
- Mutasiya `security/` və kernel-i yazmır
- VLM/LLM yoxdursa uğur uydurulmur
