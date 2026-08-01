# AI System - Süni İntellekt Platforması

![AI System Logo](https://img.icons8.com/color/48/000000/artificial-intelligence.png)

**AI System** - Maşın öyrənməsi və dərin öyrənmə modellərini hazırlamaq, öyrətmək, qiymətləndirmək və deploy etmək üçün **tamamilə modullu** Python platforması.

---

## 📌 Məzmun

1. [Nədir?](#-nədir)
2. [Xüsusiyyətləri](#-xüsusiyyətləri)
3. [Quraşdırma](#-quraşdırma)
4. [İstifadə Qısa Başlanğıc](#-istifadə-qısa-başlanğıc)
5. [Arxitektura](#-arxitektura)
6. [Modullar](#-modullar)
7. [İnterfeyslər](#-interfeyslər)
8. [Nümayişlər](#-nümayişlər)
9. [Testlər](#-testlər)
10. [Dokumentasiya](#-dokumentasiya)
11. [Təminat və Kömək](#-təminat-və-kömək)

---

## 🤔 Nədir?

**AI System** - Süni İntellekt (SI) layihələri üçün hazırlanmış **tamamilə modullu** Python platformasıdır. Bu platforma ilə:

- **Məlumatları emal edin** (təmizləyin, normalizasiya edin, artırın)
- **Modelləri öyrədin** (Maşın Öyrənməsi və Dərin Öyrənmə)
- **Modelləri qiymətləndirin** (metrikalar, izahatlar)
- **Proqnozlaşdırın** (prediction, inference)
- **Deploy edin** (REST API, CLI, GUI)

---

## ✨ Xüsusiyyətləri

### 🎯 Əsas Xüsusiyyətlər

- **Modullu Arxitektura**: Hər bir komponent ayrı moduldur (data, models, training, inference)
- **Genişləndiriləbilən**: Yeni modellər, preprocessinq adımları və ya optimizatorlar asanlıqla əlavə edilə bilər
- **Çoxsaylı Modellər**: ML (Linear Regression, Random Forest, K-Means) və DL (NN, CNN, RNN, Transformer)
- **Çoxsaylı Optimizatorlar**: Adam, SGD, AdamW, RAdam
- **Çoxsaylı Loss Funksiyaları**: MSE, CrossEntropy, Focal Loss, Contrastive Loss
- **Çoxsaylı Metrikalar**: Accuracy, Precision, Recall, F1, ROC AUC
- **Explainable AI (XAI)**: LIME və SHAP izahatları
- **Çoxsaylı İstifadəçi Interfeysləri**: CLI, GUI (Tkinter), Web (Flask), REST API (FastAPI)
- **Visualizasiya**: Matplotlib və Seaborn ilə qrafiklər
- **Testlər**: Unit, Integration, Performance testləri

### 🔧 Texniki Xüsusiyyətlər

- **Python 3.8+** dəstəyi
- **PyTorch** əsaslı dərin öyrənmə
- **Scikit-learn** əsaslı maşın öyrənməsi
- **NumPy** və **Pandas** əsaslı məlumat emalı
- **SQLite** və **CSV** əsaslı məlumat saxlama
- **GPU Dəstəyi**: CUDA ilə paralel hesablama

---

## 🚀 Quraşdırma

### 1. Repository-nu Klonlayın

```bash
cd /workspace
git clone https://github.com/Mireyyub/zenthon.git
cd zenthon
```

### 2. Virtual Environment Yaradın (Tövsiyə olunur)

```bash
# Python 3.8+ tələb olunur
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Asılılıqları Quraşdırın

```bash
pip install -r requirements.txt
```

**Requirements.txt məzmunu:**
```
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
torch>=1.9.0
torchvision>=0.10.0
Pillow>=8.0.0
opencv-python>=4.5.0
fastapi>=0.70.0
uvicorn>=0.15.0
flask>=2.0.0
matplotlib>=3.4.0
seaborn>=0.11.0
scipy>=1.7.0
psutil>=5.8.0
GPUtil>=1.4.0
```

### 4. Quraşdırmanı Yoxlayın

```bash
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

---

## 📖 İstifadə Qısa Başlanğıc

### 1. Məlumatları Hazırlayın

```python
import numpy as np
import pandas as pd
from data.preprocessing.clean import DataCleaner
from data.preprocessing.normalize import DataNormalizer

# Məlumatları yükləyin
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

#### Maşın Öyrənməsi Modeli

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

#### Dərin Öyrənmə Modeli

```python
import torch
from models.dl.nn.simple_nn import SimpleNN
from training.trainers.supervised_trainer import SupervisedTrainer

# Məlumatları PyTorch tensor-lərinə çevirin
X_tensor = torch.from_numpy(X_norm).float()
y_tensor = torch.from_numpy(y).float().unsqueeze(1)

# Modeli yaradın
model = SimpleNN(input_size=X_norm.shape[1], hidden_sizes=[64, 32], output_size=1)

# Trainer-i yaradın
trainer = SupervisedTrainer(
    model=model,
    optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
    criterion=torch.nn.MSELoss(),
)

# Modeli öyrədin
history = trainer.train(
    X_train=X_tensor,
    y_train=y_tensor,
    epochs=10,
    batch_size=32,
)

# Proqnozlaşdırın
predictions = trainer.predict(X_tensor)
```

### 3. REST API ilə İstifadə

```python
from inference.api.fastapi_app import run_api

# API-ni başladın
run_api(host="0.0.0.0", port=8000)
```

Sonra **http://localhost:8000/docs** ünvanına keçərək API sənədlərini görə bilərsiniz.

### 4. CLI ilə İstifadə

```bash
# Model öyrədin
python -m interfaces.cli.main_cli train --model linear_regression --data train.csv --target y

# Proqnozlaşdırın
python -m interfaces.cli.main_cli predict --model linear_regression --data test.csv

# Qiymətləndirin
python -m interfaces.cli.main_cli evaluate --model linear_regression --data test.csv --target y

# Sistem məlumatını göstərin
python -m interfaces.cli.main_cli info
```

### 5. GUI ilə İstifadə

```bash
python -m interfaces.gui.main_gui
```

---

## 🏗️ Arxitektura

```
AI_System/
│
├── core/                          # Əsas sistem komponentləri
│   ├── config.py                 # Konfiqurasiya idarəetməsi
│   ├── logger.py                 # Log sistemləri
│   └── kernel.py                 # Sistem resursları
│
├── data/                          # Məlumat emalı
│   ├── preprocessing/             # Məlumatların hazırlanması
│   │   ├── clean.py              # Təmizləmə
│   │   ├── normalize.py          # Normalizasiya
│   │   └── augment.py            # Artırma
│   └── storage/                  # Saxlama
│       └── database.py           # Database əməliyyatları
│
├── models/                       # Modellər
│   ├── ml/                       # Maşın Öyrənməsi
│   │   ├── supervised/           # Nəzarətli öyrənmə
│   │   │   ├── linear_regression.py
│   │   │   └── random_forest.py
│   │   └── unsupervised/         # Nəzarətsiz öyrənmə
│   │       └── kmeans.py
│   │
│   └── dl/                       # Dərin Öyrənmə
│       ├── nn/                   # Neuron şəbəkələri
│       │   └── simple_nn.py
│       ├── cnn/                  # Konvolusyon
│       │   └── simple_cnn.py
│       ├── rnn/                  # Rekurrent
│       │   └── simple_rnn.py
│       └── transformer/          # Transformer
│           └── simple_transformer.py
│
├── training/                     # Öyrədilmə
│   ├── trainers/                 # Öyrədicilər
│   │   └── supervised_trainer.py
│   ├── optimizers/               # Optimizatorlar
│   │   └── custom_optimizers.py
│   ├── loss_functions/          # Itki funksiyaları
│   │   └── custom_losses.py
│   └── metrics/                 # Metrikalar
│       └── classification_metrics.py
│
├── inference/                    # Proqnozlaşdırma
│   ├── predictors/               # Proqnozlaşdırıcılar
│   │   └── model_predictor.py
│   ├── explainers/               # İzahat sistemləri
│   │   ├── lime_explainer.py
│   │   └── shap_explainer.py
│   └── api/                      # API
│       └── fastapi_app.py
│
├── interfaces/                   # İstifadəçi interfeysləri
│   ├── cli/                      # Komanda sətri
│   │   └── main_cli.py
│   ├── gui/                      # Qrafik interfeys
│   │   └── main_gui.py
│   └── web/                      # Veb interfeys
│       └── web_interface.py
│
├── utils/                        # Köməkçi alətlər
│   ├── math/                     # Riyazi funksiyalar
│   │   ├── linear_algebra.py
│   │   └── statistics.py
│   ├── visualization/             # Vizualizasiya
│   │   └── plotting.py
│   └── helpers/                 # Köməkçi funksiyalar
│       └── file_utils.py
│
├── tests/                        # Testlər
│   ├── unit/                     # Vahid testlər
│   ├── integration/              # İntegerasiya testləri
│   └── performance/              # Performans testləri
│
├── docs/                         # Sənədləşdirmə
│   ├── architecture.md
│   └── README.md
│
└── README.md
```

**Detal Arxitektura Sənədi:** [docs/architecture.md](docs/architecture.md)

---

## 📦 Modullar

### 🔹 Core Module

| Fayl | Təsvir |
|------|--------|
| `config.py` | Sistem konfiqurasiyası |
| `logger.py` | Log sistemləri |
| `kernel.py` | Sistem resursları |

### 🔹 Data Module

| Qovluq | Fayl | Təsvir |
|--------|------|--------|
| `preprocessing/` | `clean.py` | Məlumatların təmizlənməsi |
| `preprocessing/` | `normalize.py` | Normalizasiya |
| `preprocessing/` | `augment.py` | Artırma (data augmentation) |
| `storage/` | `database.py` | Database əməliyyatları |

### 🔹 Models Module

| Qovluq | Fayl | Təsvir |
|--------|------|--------|
| `ml/supervised/` | `linear_regression.py` | Xətti regressiya |
| `ml/supervised/` | `random_forest.py` | Random Forest |
| `ml/unsupervised/` | `kmeans.py` | K-Means clustering |
| `dl/nn/` | `simple_nn.py` | Sadə neuron şəbəkəsi |
| `dl/cnn/` | `simple_cnn.py` | CNN |
| `dl/rnn/` | `simple_rnn.py` | RNN, LSTM, GRU |
| `dl/transformer/` | `simple_transformer.py` | Transformer |

### 🔹 Training Module

| Qovluq | Fayl | Təsvir |
|--------|------|--------|
| `trainers/` | `supervised_trainer.py` | Nəzarətli öyrənmə üçün öyrədici |
| `optimizers/` | `custom_optimizers.py` | AdamW, SGDW, RAdam |
| `loss_functions/` | `custom_losses.py` | Focal Loss, Contrastive Loss |
| `metrics/` | `classification_metrics.py` | Accuracy, Precision, Recall, F1 |

### 🔹 Inference Module

| Qovluq | Fayl | Təsvir |
|--------|------|--------|
| `predictors/` | `model_predictor.py` | Universal proqnozlaşdırıcı |
| `explainers/` | `lime_explainer.py` | LIME izahatları |
| `explainers/` | `shap_explainer.py` | SHAP izahatları |
| `api/` | `fastapi_app.py` | REST API |

### 🔹 Interfaces Module

| Qovluq | Fayl | Təsvir |
|--------|------|--------|
| `cli/` | `main_cli.py` | Komanda sətri interfeysi |
| `gui/` | `main_gui.py` | Qrafik interfeys (Tkinter) |
| `web/` | `web_interface.py` | Veb interfeys (Flask) |

### 🔹 Utils Module

| Qovluq | Fayl | Təsvir |
|--------|------|--------|
| `math/` | `linear_algebra.py` | Xətti cəbr əməliyyatları |
| `math/` | `statistics.py` | Statistika funksiyaları |
| `visualization/` | `plotting.py` | Qrafiklər (Matplotlib, Seaborn) |
| `helpers/` | `file_utils.py` | Fayl əməliyyatları |

### 🔹 Tests Module

| Qovluq | Fayl | Təsvir |
|--------|------|--------|
| `unit/` | `test_core.py` | Core modulu üçün vahid testlər |
| `unit/` | `test_data.py` | Data modulu üçün vahid testlər |
| `unit/` | `test_models.py` | Models modulu üçün vahid testlər |
| `integration/` | `test_training_pipeline.py` | Öyrədilmə pipeline-i üçün integerasiya testləri |
| `performance/` | `test_model_performance.py` | Performans testləri |

---

## 🖥️ İnterfeyslər

### 1. CLI (Komanda Sətri Interfeysi)

**İstifadə:**
```bash
# Model öyrədin
python -m interfaces.cli.main_cli train --model linear_regression --data train.csv --target y

# Proqnozlaşdırın
python -m interfaces.cli.main_cli predict --model linear_regression --data test.csv

# Qiymətləndirin
python -m interfaces.cli.main_cli evaluate --model linear_regression --data test.csv --target y

# Sistem məlumatını göstərin
python -m interfaces.cli.main_cli info

# Modelləri siyahıya çıxarın
python -m interfaces.cli.main_cli list_models
```

**Dəstək olunan modellər:**
- `linear_regression`
- `random_forest`
- `kmeans`
- `simple_nn`

### 2. GUI (Qrafik İstifadəçi Interfeysi)

**İstifadə:**
```bash
python -m interfaces.gui.main_gui
```

**Xüsusiyyətləri:**
- Məlumatların yüklənməsi və önizlənməsi
- Model öyrədilməsi
- Proqnozlaşdırma
- İzahatların generasiyası
- Logların göstərilməsi

### 3. Web İnterfeysi (Flask)

**İstifadə:**
```bash
python -m interfaces.web.web_interface
```

**Səhifələr:**
- `/` - Əsas səhifə
- `/train` - Model öyrədilməsi
- `/predict` - Proqnozlaşdırma
- `/explain` - İzahat generasiyası

### 4. REST API (FastAPI)

**İstifadə:**
```bash
python -m inference.api.fastapi_app
```

**API Endpoint-ləri:**
- `GET /` - Əsas səhifə
- `GET /health` - Sistem sağlamlığı
- `GET /models` - Modellərin siyahısı
- `POST /register_model` - Model qeydiyyatı
- `POST /predict` - Proqnozlaşdırma
- `POST /predict_image` - Şəkil üzrə proqnozlaşdırma
- `POST /explain` - İzahat generasiyası
- `POST /register_explainer` - İzahatçı qeydiyyatı
- `POST /api/upload` - Fayl yükləmə

**API Sənədləri:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🎯 Nümayişlər

### 1. Maşın Öyrənməsi Modeli (Linear Regression)

```python
import numpy as np
from models.ml.supervised.linear_regression import LinearRegression

# Məlumatları yaradın
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([3, 5, 7, 9, 11])  # y = 2x + 1

# Modeli yaradın və öyrədin
model = LinearRegression()
model.fit(X, y, method="normal")

# Proqnozlaşdırın
predictions = model.predict(X)
print("Predictions:", predictions)

# Qiymətləndirin
score = model.score(X, y)
print(f"R-squared: {score:.4f}")
```

### 2. Dərin Öyrənmə Modeli (SimpleNN)

```python
import torch
from models.dl.nn.simple_nn import SimpleNN
from training.trainers.supervised_trainer import SupervisedTrainer

# Məlumatları yaradın
X = torch.randn(100, 10)
y = torch.randn(100, 1)

# Modeli yaradın
model = SimpleNN(input_size=10, hidden_sizes=[64, 32], output_size=1)

# Trainer-i yaradın
trainer = SupervisedTrainer(
    model=model,
    optimizer=torch.optim.Adam(model.parameters(), lr=0.001),
    criterion=torch.nn.MSELoss(),
)

# Modeli öyrədin
history = trainer.train(X_train=X, y_train=y, epochs=10, batch_size=32)

# Proqnozlaşdırın
predictions = trainer.predict(X)
print("Predictions:", predictions)
```

### 3. CNN Modeli (SimpleCNN)

```python
import torch
from models.dl.cnn.simple_cnn import SimpleCNN

# Modeli yaradın (MNIST üçün)
model = SimpleCNN(in_channels=1, num_classes=10)

# Təlimat üçün məlumat
X = torch.randn(32, 1, 28, 28)  # 32 şəkil, 1 kanal, 28x28

# Proqnozlaşdırın
outputs = model(X)
print("Outputs shape:", outputs.shape)  # (32, 10)
```

### 4. RNN Modeli (SimpleRNN)

```python
import torch
from models.dl.rnn.simple_rnn import SimpleRNN

# Modeli yaradın
model = SimpleRNN(
    input_size=10,
    hidden_size=32,
    output_size=1,
    rnn_type="lstm",
)

# Təlimat üçün məlumat
X = torch.randn(32, 20, 10)  # 32 seriya, 20 addım, 10 feature

# Proqnozlaşdırın
outputs = model(X)
print("Outputs shape:", outputs.shape)  # (32, 1)
```

### 5. Transformer Modeli

```python
import torch
from models.dl.transformer.simple_transformer import SimpleTransformer

# Modeli yaradın
model = SimpleTransformer(
    vocab_size=1000,
    d_model=256,
    num_heads=8,
    num_layers=4,
    num_classes=10,
)

# Təlimat üçün məlumat
X = torch.randint(0, 1000, (32, 50))  # 32 cümlə, 50 token

# Proqnozlaşdırın
outputs = model(X)
print("Outputs shape:", outputs.shape)  # (32, 10)
```

### 6. LIME İzahatı

```python
import numpy as np
from models.ml.supervised.linear_regression import LinearRegression
from inference.explainers.lime_explainer import LIMEExplainer

# Modeli yaradın və öyrədin
X = np.random.randn(100, 5)
y = np.random.randn(100)
model = LinearRegression()
model.fit(X, y)

# LIME izahatçısını yaradın
explainer = LIMEExplainer(
    model=model,
    feature_names=[f"feature_{i}" for i in range(5)],
)

# İzahat generasiya edin
x_instance = X[0]
explanation = explainer.explain_instance(x_instance)

# İzahatı göstərin
print(explainer.visualize_explanation(explanation))
```

### 7. REST API ilə Proqnozlaşdırma

```python
import requests
import json

# API-ya müraciət edin
url = "http://localhost:8000/predict"
data = {
    "model_name": "linear_regression",
    "data": [[1.0, 2.0, 3.0, 4.0, 5.0]],
}

response = requests.post(url, json=data)
result = response.json()
print("Prediction:", result["prediction"])
```

---

## 🧪 Testlər

### Testləri İşə Salın

```bash
# Bütün testləri işə salın
python -m pytest tests/

# Yalnız vahid testləri işə salın
python -m pytest tests/unit/

# Yalnız integerasiya testlərini işə salın
python -m pytest tests/integration/

# Yalnız performans testlərini işə salın
python -m pytest tests/performance/

# Spesifik test faylını işə salın
python -m pytest tests/unit/test_core.py
```

### Test Coverage

```bash
# Test coverage-i yoxlayın
pip install pytest-cov
pytest --cov=AI_System tests/
```

---

## 📚 Dokumentasiya

- **[Arxitektura Sənədi](docs/architecture.md)** - Detal sistem arxitekturası
- **[API Reference](docs/api_reference.md)** - API sənədləri (qurulacaq)
- **[Tutorials](docs/tutorials/)** - Təlimatlar və nümayişlər (qurulacaq)

---

## 🤝 Təminat və Kömək

### Təminat

Bu layihə **MIT License** altında buraxılır. Ətraflı məlumat üçün [LICENSE](LICENSE) faylına baxın.

### Kömək

- **Sualınız var?** GitHub Issues vasitəsi ilə sual verin
- **Xəta tapdınız?** GitHub Issues vasitəsi ilə xəta bildirin
- **Təkmilləşdirmə təklifi?** Pull Request göndərin

### Əlaqə

- **Email**: [mireyyub@gmail.com](mailto:mireyyub@gmail.com)
- **GitHub**: [Mireyyub](https://github.com/Mireyyub)
- **LinkedIn**: [Mireyyub](https://www.linkedin.com/in/mireyyub)

---

## 📝 Versiya Tarixçəsi

| Versiya | Tarix | Dəyşikliklər |
|---------|-------|--------------|
| 1.0.0 | 2024-01-01 | İlk buraxılış |

---

## 🎉 Nəyi Öyrənə Bilərsiniz?

Bu layihə ilə:

1. **Maşın Öyrənməsi** - Linear Regression, Random Forest, K-Means
2. **Dərin Öyrənmə** - Neural Networks, CNN, RNN, Transformer
3. **Məlumat Emalı** - Təmizləmə, Normalizasiya, Artırma
4. **Model Öyrədilməsi** - Optimizatorlar, Loss Funksiyaları, Metrikalar
5. **Proqnozlaşdırma** - Predictors, Explainers (LIME, SHAP)
6. **API Development** - FastAPI, Flask
7. **İstifadəçi Interfeysləri** - CLI, GUI, Web
8. **Test Yazma** - Unit, Integration, Performance Tests
9. **Visualizasiya** - Matplotlib, Seaborn
10. **Sistem Dizaynı** - Modullu Arxitektura

---

## 🚀 Növbəti Addımlar

1. **Layihəni klonlayın və quraşdırın**
2. **Nümayişləri sınayın**
3. **Öz modellərinizi əlavə edin**
4. **API-ni deploy edin**
5. **Təkmilləşdirmə təklifləri göndərin**

---

**Uğurlar!** 🎉

Bu layihə ilə **Süni İntellekt** sahəsində böyük addımlar atacaqsınız. Hansı sualınız varsa, çəkinmədən əlaqə saxlayın!

---

*"Süni İntellekt - Gələcəyin Texnologiyası"* 🤖
