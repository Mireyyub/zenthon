# Zenthon Çoxdilli Mühəndislik Memarlığı

## Qərar Prinsipi

Zenthon bütün proqramlaşdırma dillərini eyni işə zorla daxil etmir. Hər dil yalnız **performans, platforma inteqrasiyası, təhlükəsizlik və ya inkişaf sürəti üzrə ölçülə bilən üstünlük** verdikdə istifadə olunur. Sistem işə düşmək üçün bir native kompilyatora və ya xarici servisa məcburi bağlı olmur; hər sürətləndirmənin Python fallback-i vardır.

> **Əsas qayda:** Python funksional nüvəni və AI orkestratorunu idarə edir. Native və platforma-dil komponentləri yalnız aydın müqavilə, vaxt limiti və geri dönüş yolu ilə bağlanır.

## Dil-Rol Matrisi

| Dil / texnologiya | Zenthon-da rol | Nə zaman seçilir | Məcburi deyil, çünki |
|---|---|---|---|
| **Python** | Agentlər, lokal LLM adapteri, AI/ML, FastAPI, Tkinter GUI, təhlükəsiz fallback | Bütün əsas AI və avtomatlaşdırma axınları | Bu, standart işləmə yoludur |
| **TypeScript** | Web Command Center, tRPC müqavilələri, browser UX | Web və mobil UI üçün | Masaüstü lokal icra ondan asılı deyil |
| **Rust** | Yaddaş-təhlükəsiz native nüvə; deterministik mətn, hash, indeks və byte əməliyyatları | Profil nəticəsi CPU darboğazını təsdiqləyəndə | Python adapteri binary yoxdursa avtomatik işləyir |
| **C/C++** | SIMD, OpenCV/PyTorch native uzantıları, intensiv görüntü/audio kernel-ləri | Profil və ya kitabxana bunu tələb etdikdə | Birbaşa GUI və agent məntiqi üçün istifadə edilmir |
| **Go** | Yüngül, paralel lokal gateway və uzunmüddətli I/O xidməti | Bir çox lokal işçi və stream I/O lazım olduqda | Sadə lokal API Python-da qalır |
| **C#/.NET** | Windows shell, enterprise identity, Windows xidmət və hardware API-ləri | Windows-a xas inteqrasiya tələb olunanda | Çarpaz-platforma AI nüvəsi Python olaraq qalır |
| **Kotlin/Java** | Android native modul, cihaz API-ləri və arxa plan işləri | Expo-native modul çatmadıqda | Web və Windows tətbiqi buna bağlı deyil |
| **Swift** | iOS native modul, Siri/Shortcuts və təhlükəsiz cihaz API-ləri | iOS-a xas imkan lazım olduqda | Android/Web/Windows axınlarını bloklamır |
| **SQL** | Davamlı sessiya, audit və axtarış indeksi | Yerli və ya server məlumat yaddaşı tələb olunanda | Hesablama məntiqi SQL-ə köçürülmür |
| **PowerShell / Bash** | Təkrarlana bilən Windows/Linux qurma və yoxlama | Paketləmə və əməliyyat avtomatlaşdırması | Biznes məntiqi skriptlərdə saxlanmır |

## Native-Core Müqaviləsi

Native komponentlər `native_core` Python adapteri ilə çağırılır. Adapter yalnız allowlist-dəki deterministik əməliyyatları çağırır: `normalize_text`, `fingerprint`, `token_metrics` və sonrakı profil-təsdiqli əməliyyatlar. İcra faylı aşağıdakı xüsusiyyətlərə malik olmalıdır:

1. JSON giriş-çıxış müqaviləsi istifadə edir.
2. Müddət limiti və maksimum giriş ölçüsü tətbiq edilir.
3. Xəta, timeout və ya binary yoxluğu zamanı Python fallback-i qaytarılır.
4. Qeyri-müəyyən kod icrası, shell interpolation və istifadəçi yolunun icrası qadağandır.
5. Sağlamlıq hesabatı hər əməliyyatın mənbəyini (`python-fallback` və ya `native-binary`) göstərir.

## İcra Yol Xəritəsi

| Mərhələ | Təkmilləşdirmə | Qəbul meyarı |
|---|---|---|
| **A — Baza** | Python native-core adapteri, sağlamlıq hesabatı və testlər | Binary olmadan eyni nəticə alınır |
| **B — Rust** | İstəyə bağlı `zenthon-native-core` CLI prototipi | Rust binary aktiv olanda adapter onu istifadə edir; fallback testləri keçər |
| **C — Platforma** | Windows üçün .NET, Android üçün Kotlin, iOS üçün Swift körpüləri | Hər modul yalnız hədəf platformada paketlənir |
| **D — Performans** | C/C++ və ya Rust kernel optimizasiyası | Profil nəticəsində ölçülə bilən fayda var; regressiya və memory testləri keçər |
| **E — Xidmətlər** | Go lokal gateway və stream işçiləri | Yalnız paralel I/O yükü bunu əsaslandırdıqda aktivləşir |

## Qadağan Edilən Yanaşmalar

Arxitektura “bütün dilləri işlətmək” naminə funksiyanı təkrarlamır, dilə görə məlumat kopyalamır və native komponenti məcburi asılılıq etmir. Heç bir native adapter agentin icazəsiz fayl yazma, proses açma və ya özünü dəyişdirmə səlahiyyətini genişləndirmir.
