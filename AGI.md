# Leon və AGI — dürüst xəritə

**Leon AGI deyil.** Bu sənəd marketinq deyil; istiqamət və sərhədlərdir.

## İcra olunmuş istiqamət addımları (1–4)

| # | Addım | Status |
|---|--------|--------|
| 1 | Geniş curriculum (math/language/social) | ✅ Vol 04–06 |
| 2 | Transfer eval (source→target zero-shot) | ✅ `evaluation/transfer.py` |
| 3 | Long-horizon planner + world state | ✅ `long_horizon_plan` + `world_state` |
| 4 | Human evaluation suite | ✅ `evaluation/human_suite.py` |

```bash
python -m interfaces.cli.main_cli teach-volume 04
python -m interfaces.cli.main_cli eval-ext transfer --sources 01,02 --target 03
python -m interfaces.cli.main_cli eval-ext long --volumes 01,02,03 --run
python -m interfaces.cli.main_cli eval-ext human
```

## Hələ AGI olmayanlar

- Open-world autonomy
- Robust multi-domain transfer (ölçülür, həll olunmayıb)
- Human-level multimodal
- Reliable multi-day goal pursuit

## Cognitive Cycle

PODALR: Perceive → Orient → Decide → Act → Learn → Reflect

`agi_claim` həmişə `false` qalır.
