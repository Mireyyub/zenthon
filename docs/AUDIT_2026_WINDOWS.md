# Leon AI Platform — Windows Masaüstü Denetimi

**Tarih:** 27 Ağustos 2026
**Kapsam:** `Mireyyub/zenthon` ana dalı, commit `bc92165`
**Sonuç:** Mevcut çalışma, korunmaya değer bir **v0.7 bilişsel platform prototipidir**. Tek bilişsel yol, güvenlik geçidi, bellek katmanları, GUI, API ve Windows paketleme var; ancak Windows öncelikli gerçek ürün standardına erişmek için çekirdek sağlamlaştırma, işlem dışı olay akışı, masaüstü ilk çalıştırma deneyimi ve paketleme doğrulamasına ihtiyaç vardır.

> Bu rapor yalnızca kaynak incelemesi ve çalıştırılan denetimlerden elde edilen kanıtları içerir. Bir bileşen mevcut olsa dahi, çalıştırılmadan veya testle korunmadan üretime hazır kabul edilmez.

## Denetim Özeti

| Alan | Doğrulanan durum | Ürün olgunluğu | Öncelikli işlem |
|---|---|---:|---|
| Kaynak yapı | Temel dalda 413 izlenen dosya; çalışma ağacında 232 üretim Python modülü ve 34 test dosyası | Orta | Kanonik ve legacy sınırlarını koru |
| Başlatma | `run.py --desktop`, GUI ile local-only FastAPI bridge'i aynı yaşam döngüsünde başlatıyor | Orta | Windows GUI açılış/kapanış smoke testi ve ilk çalıştırma akışı ekle |
| Bilişsel çekirdek | `BrainOrchestrator → ReasoningEngine` tek giriş yolunu kullanıyor | Orta | Bağımlılık enjeksiyonu, hata türleri ve operasyon telemetrisi ekle |
| Reasoning | Müfredat/fact/graph/bellek kanıtı, çatışma → `UNKNOWN`, iz kaydı mevcut | Orta | Daha geniş stratejiler ve yapılandırılmış kanıt kökeni ekle |
| Bellek | Çalışma, vektör, semantik ve isteğe bağlı episodik/uzun dönem katmanlar var | Orta | Kalıcı bellek için güven/evidence doğrulamasını varsayılan hale getir |
| Araç güvenliği | Allowlist, izin, path sandbox, redakte audit kaydı ve tipli risk/onay politikası var | Orta | Araç-başına giriş/çıkış şeması ve işlem-izole timeout uygula |
| Olay sistemi | Thread-safe event bus, atomik sınırlı kalıcı read model ve loopback salt-okunur feed var | Orta | GUI görev merkezi, retention telemetrisi ve Windows kapatma senaryosu ekle |
| Windows GUI | Tkinter Command Center; Think/Teach/Improve/Status, Operations, Local Setup, arka plan işçileri ve loopback API durum göstergesi var | Orta | Gerçek Windows görünüş/kapanış denetimi ve erişilebilirlik gözden geçirmesi ekle |
| API | Sağlık, reasoning, agent, öğretme, çoklu ortam, yapılandırılmış hata ve yerel event feed uçları var | Orta | Yerel token/izin modeli ile görev/agent/bellek salt-okunur yüzeylerini ekle |
| Paketleme | PyInstaller + NSIS scripti, kısayollar/kaldırıcı ve birleşik desktop giriş noktası var | Kısmi | İlk çalıştırma, Windows paket smoke testi ve Windows CI ekle |
| Legacy ML | `models/`, `training/`, klasik inference ve web UI legacy olarak ayrılmış | Bilinçli legacy | Silmeden önce adaptör, taşıma planı ve test oluştur |

## Çalıştırılan Doğrulamalar

| Denetim | Sonuç | Kanıt / not |
|---|---|---|
| Tüm Python kaynaklarının derlenmesi | **Geçti** | Başlangıçta `inference/explainers/shap_explainer.py` içinde geçersiz `\\n` karakteri bulundu ve düzeltildi. Ardından `compileall` temiz geçti. |
| Proje yerel kurulumu | **Geçti** | `python3 run.py --check`, proje içi `.venv` oluşturarak `requirements.txt` bağımlılıklarını kurdu. |
| Çekirdek smoke akışı | **Geçti / LLM kontrolü** | `run.py --check` ile başlatma, `ReasoningEngine` yolu, öğretme, kalıcılık ve checkpoint adımları başarılı oldu. Yerel LLM endpointi erişilemedi; uygulama kontrollü fallback ile `overall_ok: true` sonucu verdi. |
| Tam Python test paketi | **Geçti** | İzole Python 3.12 ortamında `164 passed, 10 warnings in 9.12s`. Uyarıların ikisi legacy ML alanları, üçünün kaynağı gelecekte kaldırılacak Pillow `getdata()` API'sidir. |
| RAG Azerbaycan Türkçesi çekim geri çağırması | **Geçti** | Güvenli, en az dört karakterli iki yönlü kök/prefix eşleme eklendi; `meyvə` sorgusu `meyvədir` içeren bağlamı geri çağırıyor. Kısa terimler kapsam dışı tutularak yanlış pozitif riski sınırlandı. |
| Görsel no-path hata sözleşmesi | **Geçti** | Bir dosya yolu olmadan görseli betimleme isteği artık açıkça desteklenmediğini bildiriyor; eksik girdiyi başarılı bir analiz gibi göstermiyor. |
| Yerel event read model ve API | **Geçti** | Kalıcılık, sınırlandırma, cursor, diskten yeniden yükleme redaksiyonu, loopback reddi ve HTTP projection testleri başarılıdır; read model ham prompt, cevap veya reasoning saklamaz. |
| Araç sözleşmesi ve API hata modeli | **Geçti** | 18 odaklı testte araç risk/timeout/onay metadatası, onay reddi, audit argüman redaksiyonu ve API'nin yapılandırılmış güvenlik hatası doğrulandı. |
| Birleşik desktop runtime | **Geçti / GUI CHECK** | Boş bir loopback portunda FastAPI hizmeti gerçekten açıldı, `GET /` yanıtı doğrulandı ve servis nizamlı dayandırıldı. Başsız Linux ortamında Tkinter pəncərəsi görünüş testi edilmedi; bu doğrulama Windows 11 cihazında ayrıca yapılacaktır. |
| Geçici günlük dizini dayanıklılığı | **Geçti** | Testte silinen geçici günlüğe bağlı `FileHandler` bir sonraki yazımdan önce kaldırılıyor; bu sayede masaüstü runtime sonrasında kalan testler `FileNotFoundError` ile bozulmuyor. |
| İlk çalıştırma profili | **Geçti / GUI CHECK** | Atomic yerel ayar kaydı, data konumu/model/event tercihi, dosya-sistemi kökü reddi, güvenli hardware önerisi ve nonlocal LLM endpointinin ilk-run ekranından hiç sorgulanmaması test edildi. GUI sihirbazı başsız ortamda görsel olarak doğrulanmadı. |
| Paket giriş ve bridge smoke | **Geçti (kaynak çalışma zamanı)** | Paket girişinin `--smoke` ve `--bridge-smoke` kipleri, gerçek dinamik loopback portunda çalışan API ile test edildi. Windows EXE/NSIS artefaktı bu Linux ortamında üretilemez; Windows CI ve bağlı Windows 11 smoke kapısı eklendi. |

## Mimari Harita

```text
Windows GUI / CLI / FastAPI
          │
          ▼
BrainOrchestrator
          ▼
ReasoningEngine
          ▼
Curriculum + Facts + Graph + Memory + opsiyonel LLM
          ▼
Planner + Agent Manager + Security Gate + Tool Registry
          ▼
Execution / Evaluation / Reflection / Learning
          ▼
data/leon/ (traces, plans, audit, memory, learning, checkpoints)
```

Bu yol, kullanıcı sorguları için tek reasoning girişini koruduğu için mimarinin en değerli tarafıdır. Yeni UI veya hizmetler bu yolu atlamamalı; sadece açık arayüzler ve olaylar yoluyla bağlanmalıdır.

## Bağımlılık ve Teknik Borç Haritası

| Risk | Kanıt | Etki | Güvenli iyileştirme |
|---|---|---|---|
| Çift bağımlılık kaynağı | Poetry metadata ve pip requirement profilleri birlikte korunuyor | Sürüm değişimlerinde paralel bakım gerekir | Python 3.10–3.12 desteğini sabit tut; sürüm yükseltmelerinde `requirements-full.txt` ile Windows CI'yı çalıştır |
| Ağır varsayılan yük | Torch, OpenCV, SciPy gibi paketler legacy ML/vision için gerekli | Düşük donanımda ilk açılış ve paket boyutu | **Azaltıldı:** default `requirements.txt` core'dur; ML/vision/full profil dosyaları opsiyoneldir. Windows release full profili bilinçli kullanır |
| Olay sürekliliği sınırı | Read model disk üzerinde yalnız son olayları saklar; tek süreçteki event bus anlıktır | Uygulama kapanış/kurtarma telemetrisi ve ileri olay dağıtımı sınırlı | GUI+API birleşik lifecycle, retention görünümü ve kapatma smoke testi |
| Araç sözleşmesi kapsamı | Risk, timeout, onay ve redaksiyon metadatası var; parametre doğrulaması geneldir | Her araç için kesin giriş/çıkış şeması ve iptal garantisi yok | Şema tabanlı tool request/result ve süreç-izole timeout adapteri |
| Desktop görünüş doğrulaması | Birleşik runtime API thread'i test edilmiş olsa da başsız ortamda Tkinter pəncərəsi denetlenemiyor | Windows görünüş, odak ve kapanış davranışı belirsiz kalır | Bağlı Windows 11 cihazında `run.py --desktop` açılış/kapanış ve bridge sağlık smoke testi |
| Windows dağıtım doğrulaması | Paket scripti mevcut, Windows CI ve paket smoke yok | Kullanıcı cihazında kurulum riski | Windows GitHub Actions, installer dosya denetimi, ilk-run hatalarının loglanması |

## Eksik Yetenek Haritası

| Talep | Mevcut karşılık | Dürüst durum | İlk ürün dilimi |
|---|---|---|---|
| Donanım algılama | Başlatma logunda CPU/RAM/CUDA özeti | GUI akışı yok | Donanım profili ve düşük/balanslı/performans önerisi |
| Model yöneticisi | Ollama client/manager ve fallback | GUI'den kurulum/etkinleştirme yok | Model sağlık kartı, endpoint doğrulama, güvenli seçici |
| Kalıcı görevler | Planner ve traces | Görev merkezinde yaşam döngüsü yok | Salt-okunur görev ve olay paneli |
| Görsel/3D ortam | Omniverse adapterı ve legacy alanlar | Ürün-grade 3D ortam yok | Önce 2D cognitive graph; 3D yalnız gerçek state adapteriyle |
| Çoklu ortam | API araçları ve opsiyonel modüller | Donanım/model bağımlı; tümü doğrulanmış değil | Dosya kabul sözleşmesi, destek durumu ve failure fallback |
| Gizlilik yüzeyi | Sandbox, allowlist, audit log | Kullanıcıya anlaşılır görünürlük sınırlı | Saklanan veri, model, tool ve izin paneli |
| İlk çalıştırma | NSIS kurulum ve kısayollar | Wizard yok | Donanım → model → depolama → izin adımları |

## Önceliklendirilmiş Yol Haritası

| Sıra | Aşama | Tamamlanma kriteri |
|---:|---|---|
| 1 | Core hardening | Tipli yapılandırma, yapılandırılmış hata, kalıcı sınırlandırılmış olay deposu, güvenlik politikası ve testleri |
| 2 | Cognitive reliability | Kanıt kökeni, confidence/unknown kuralları ve bellek terfi doğrulaması |
| 3 | Desktop runtime | **Tamamlandı (Linux runtime)**: tek komutla GUI + loopback API, sağlık, log ve cleanup sözleşmesi. Windows GUI smoke doğrulaması sonraki release kapısıdır. |
| 4 | First-run experience | **Tamamlandı (kaynak runtime)**: gerçek CPU/RAM/CUDA tespiti, loopback-only model sağlık denetimi, data/izin profili ve wizard. Windows görsel smoke kapısı açıktır. |
| 5 | Windows release quality | **Kısmen tamamlandı:** PyInstaller/NSIS girişi, seçilebilir autostart, per-user data dizini, GUI-free paket smoke kipleri ve Windows CI. Gerçek EXE/installer testi ile imza/allowlist belgeleri hâlâ gereklidir. |

## Denetim Kararı

Leon'un mevcut kaynaklarını yeniden yazmadan korumak doğrudur. İlk uygulama dilimi, görünür fakat sahte bir 3D katman yerine **kalıcı olay/izleme temelini**, **birleşik Windows başlatıcısını**, **güvenli configuration ve model durumunu** güçlendirmelidir. Bu temel, modern Command Center'ın gerçek zamanlı ama güvenli bilgi kaynağı olacaktır.

## Kapanış Durumu ve Açık Borçlar

Çekirdek denetim aşaması, mevcut Linux doğrulama ortamında geçmiştir: tüm toplanan testler başarılıdır ve yerel LLM erişilemediğinde deterministik fallback korunmaktadır. Bu sonuç, Windows kurulumu, GPU/vision modeli ya da paketlenmiş GUI'nin hedef bilgisayarda doğrulandığı anlamına gelmez. Bu ayrı doğrulamalar, ürünleştirme aşamasında gerçek Windows 11 cihazında yapılmalıdır.

| Öncelik | Açık borç | Sahip olunan koruma | Sonraki doğrulama |
|---:|---|---|---|
| P1 | GUI görev merkezi için kalıcı, sınırlı olay akışı | Redakte edilmiş atomik event read model, cursor ve loopback API testleri | GUI'de event/task görünümü, retention sayaçları ve uygulama kapanış testi |
| P1 | Gerçek Windows GUI/bridge smoke testi | Başsız ortamda loopback API açılış/kapanış testi ve CLI sözleşme testi geçti | Bağlı Windows 11 cihazında `run.py --desktop`, GUI görünüşü, bridge sağlık ve kapanış doğrulaması |
| P0 | Windows paketli çalışma zamanı smoke testi | PyInstaller/NSIS betikleri mevcut | Temiz Windows 11 cihazında kurulum, açılış, kaldırma ve log doğrulaması |
| P1 | Windows first-run görünüş testi | Kaynak runtime'da hardware/model/storage/consent wizard ve Local Setup paneli mevcut | Bağlı Windows 11 cihazında wizard akışı, veri dizini seçimi ve `--desktop` görünüş/kapanış doğrulaması |
| P1 | Windows EXE ve kurulum smoke testi | PyInstaller/NSIS scripti, packaged `--smoke`/`--bridge-smoke` kipleri ve artifact CI kapısı mevcut | Windows 11'de EXE, installer, uninstall ve optional autostart testini çalıştır; gerektiğinde Microsoft SmartScreen/kurum allowlist'i için imzalama planla |
| P1 | Bağımlılık profili kabul testi | Core/ML/Vision/Full gereksinim dosyaları ve command-line profil seçimi var | Temiz Windows makinede core ve full kurulum süresi/boyutu/başlatma ölçümü |
| P1 | Bağımlılık katmanlandırması | Mevcut runtime çalışıyor | Çekirdek, vision ve geliştirme extras ayrımı ile düşük donanım kurulum testi |
| P2 | Pillow API kaldırılma uyarısı | Mevcut testler başarılı | `getdata()` çağrılarını desteklenen `get_flattened_data()` eşdeğeriyle değiştirme ve görüntü regresyon testi |
