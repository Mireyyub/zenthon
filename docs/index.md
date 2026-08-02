# Zenthon AI System

**Suni İntellekt Platforması - Tamamilə Modullu Python Platforması**

![AI System Logo](https://img.icons8.com/color/48/000000/artificial-intelligence.png)

---

## Nədir?

**Zenthon AI System** — Maşın Öyrənməsi və Dərin Öyrənmə modellərini hazırlamaq, öyrətmək, qiymətləndirmək və deploy etmək üçün **tamamilə modullu** Python platformasıdır.

Bu platforma ilə:
- **Məlumatları emal edin** (təmizləyin, normalizasiya edin, artırın)
- **Modelləri öyrədin** (Maşın Öyrənməsi və ya Dərin Öyrənmə)
- **Modelləri qiymətləndirin** (metrikalar, izahatlar)
- **Proqnozlaşdırın** (prediction, inference)
- **Deploy edin** (REST API, CLI, GUI)

---

## Xüsusiyyətləri

### Əsas Xüsusiyyətlər

- **Modullu Arxitektura**: Hər bir komponent ayrı moduldur (data, models, training, inference)
- **Genişləndiriləbilən**: Yeni modellər, preprocessing addımları və ya optimizatorlar asanlıqla əlavə edilə bilər
- **Çoxsaylı Modellər**: ML (Linear Regression, Random Forest, K-Means) və DL (NN, CNN, RNN, Transformer)
- **Çoxsaylı Optimizatorlar**: Adam, SGD, AdamW, RAdam
- **Çoxsaylı Loss Funksiyaları**: MSE, CrossEntropy, Focal Loss, Contrastive Loss
- **Çoxsaylı Metrikalar**: Accuracy, Precision, Recall, F1, ROC AUC
- **Explainable AI (XAI)**: LIME və SHAP izahatlar
- **Çoxsaylı İstifadəçi Interfeysləri**: CLI, GUI (Tkinter), Web (Flask), REST API (FastAPI)
- **Visualizasiya**: Matplotlib və Seaborn ilə qrafiklər
- **Testlər**: Unit, Integration, Performance testləri

### Texniki Xüsusiyyətlər

- **Python 3.8+** dəstəyidir
- **PyTorch** əsaslı dərin öyrənmə
- **Scikit-learn** əsaslı maşın öyrənməsi
- **NumPy** və **Pandas** əsaslı məlumat emalı
- **SQLite** və **CSV** əsaslı məlumat saxlanması
- **GPU Dəstəyidir**: CUDA ilə paralel hesablama

---

## Quraşdırma

Layihəni quraşdırmaq üçün aşağıdakı addımları izləyin:

1. **Repository-nu klonlayın:**
   ```bash
   git clone https://github.com/Mireyyub/zenthon.git
   cd zenthon
   ```

2. **Virtual Environment yaradın:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Asılılıqları quraşdırın:**
   ```bash
   pip install -r requirements.txt
   ```

---

## İstifadə Qısa Başlanğıc

### 1. Məlumatları Hazırlayın

```python
import numpy as np
import pandas as pd
from data.preprocessing.clean import DataCleaner
from data.preprocessing.normalize import DataNormalizer

# Məlumatları yükleyin
data = pd.read_csv("data.csv")
X = data.drop("target", axis=1).values
y = data["target"].values

# Məlumatları təmizləyin
cleaner = DataCleaner()
X_clean = cleaner.handle_missing_values(X, strategy="fill", fill_value=0)

# Məlumatları normalizasiya edin
normalizer = DataNormalizer()
X_norm = normalizer.z_score_normalize(X_clean)
```

### 2. Model Öyrədin

```python
from models.ml.supervised.linear_regression import LinearRegression

# Modeli yaradın
model = LinearRegression()

# Modeli öyrədin
model.fit(X_norm, y)

# Proqnozlaşdırın
predictions = model.predict(X_norm)

# Qiymətləndirin
score = model.score(X_norm, y)
print(f"R-squared: {score:.4f}")
```

---

## Arxitektura

Layihənin detallı arxitekturasını öyrənmək üçün [Arxitektura Səhifəsi](architecture.md) səhmə keçin.

---

## Dəstək

- **Sualınız var?** [GitHub Issues](https://github.com/Mireyyub/zenthon/issues) vasitəsi ilə sual verin
- **Xəta tapdınız?** [GitHub Issues](https://github.com/Mireyyub/zenthon/issues) vasitəsi ilə xəta bildirin
- **Təkmilləşdirmə təklifi?** [Pull Request](https://github.com/Mireyyub/zenthon/pulls) göndərin

---

## Lisenziya

Bu layihə **MIT License** altında buraxılır. Ətraflı məlumat üçün [LICENSE](https://github.com/Mireyyub/zenthon/blob/main/LICENSE) faylına baxın.
