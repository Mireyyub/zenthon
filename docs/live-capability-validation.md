# Canlı Qabiliyyət Yoxlaması

Son vizual yoxlama qrafiki `data/leon/reports/live_capability_validation.png` faylında saxlanır.

| Sahə | Son vəziyyət |
|---|---|
| Lokal Ollama LLM | CHECK — model faylları mövcuddur, lakin 3.8 GB RAM olan mühitdə `llama3.2:1b` server prosesi yüklənərkən dayanır və 500 qaytarır. |
| ReAct agent | PASS — təhlükəsiz zaman aləti ilə canlı cavab verdi. |
| Coding agent | PASS — LLM cavabı boş/xətalı olduqda offline faktorial fallback-i yazıb icra etdi. |
| Görüntü və səs | PASS — görüntü və səs alətlərinin altı əsas giriş nöqtəsi qeydiyyatda idi. |
| Self-mutation | PASS — yalnız keyfiyyət qapısından keçən JSONL tədris mutasiyası backup ilə tətbiq edildi. |

Kodlaşdırma agentinin `write_file` parametr sırası düzəldildi; `path||content` indi düzgün ayrılır. Bu yoxlamada 11 hədəf regression testi keçdi.
