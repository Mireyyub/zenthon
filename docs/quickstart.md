# İstifadə Qısa Başlanğıc

Bu səhifədə **Zenthon AI System**-i istifadə etmək üçün əsas nümunələr göstərilmişdir.

---

## 1. Məlumatları Hazırlama

### Məlumatların Yüklənməsi

```python
import pandas as pd

# CSV faylından məlumatları yükleyin
data = pd.read_csv("data.csv")

# Məlumatları bölün
X = data.drop("target", axis=1).values
y = data["target"].values
```

### Məlumatların Təmizlənməsi

```python
from data.preprocessing.clean import DataCleaner

cleaner = DataCleaner()

# Boş dəyərləri doldurun
X_clean = cleaner.handle_missing_values(X, strategy="fill", fill_value=0)

# və ya boş dəyərləri silin
X_clean = cleaner.handle_missing_values(X, strategy="drop")
```

### Məlumatların Normalizasiyası

```python
from data.preprocessing.normalize import DataNormalizer

normalizer = DataNormalizer()

# Z-score normalizasiyası
X_norm = normalizer.z_score_normalize(X_clean)

# Min-Max normalizasiyası
X_norm = normalizer.min_max_normalize(X_clean)
```

---

## 2. Maşın Öyrənməsi Modelləri

### Linear Regression

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

### Random Forest

```python
from models.ml.supervised.random_forest import RandomForest

# Modeli yaradın
model = RandomForest(n_estimators=100, max_depth=5)

# Modeli öyrədin
model.fit(X_norm, y)

# Proqnozlaşdırın
predictions = model.predict(X_norm)

# Qiymətləndirin
accuracy = model.score(X_norm, y)
print(f"Accuracy: {accuracy:.4f}")
```

### K-Means Clustering

```python
from models.ml.unsupervised.kmeans import KMeans

# Modeli yaradın
model = KMeans(n_clusters=3, max_iter=100)

# Modeli öyrədin
model.fit(X_norm)

# Cluster-ləri tapın
labels = model.predict(X_norm)
print(f"Cluster labels: {labels}")
```

---

## 3. Dərin Öyrənmə Modelləri

### Sadə Neuron Şəbəkəsi (SimpleNN)

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

### CNN (SimpleCNN)

```python
from models.dl.cnn.simple_cnn import SimpleCNN

# Modeli yaradın (MNIST üçün)
model = SimpleCNN(in_channels=1, num_classes=10)

# Təlimat üçün məlumat
X = torch.randn(32, 1, 28, 28)  # 32 şəkil, 1 kanal, 28x28

# Proqnozlaşdırın
outputs = model(X)
print(f"Outputs shape: {outputs.shape}")  # (32, 10)
```

### RNN (SimpleRNN)

```python
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
print(f"Outputs shape: {outputs.shape}")  # (32, 1)
```

---

## 4. Model Qiymətləndirilməsi

### Metrikaların Hesablanması

```python
from training.metrics.classification_metrics import ClassificationMetrics

# Metrikaları hesablayın
metrics = ClassificationMetrics()

# Dəyişənləri hesablayın
accuracy = metrics.accuracy(y_true, y_pred)
precision = metrics.precision(y_true, y_pred)
recall = metrics.recall(y_true, y_pred)
f1 = metrics.f1_score(y_true, y_pred)

print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
```

---

## 5. Explainable AI (XAI)

### LIME İzahatı

```python
from models.ml.supervised.linear_regression import LinearRegression
from inference.explainers.lime_explainer import LIMEExplainer

# Modeli yaradın və öyrədin
model = LinearRegression()
model.fit(X_norm, y)

# LIME izahatçısını yaradın
explainer = LIMEExplainer(
    model=model,
    feature_names=[f"feature_{i}" for i in range(X_norm.shape[1])],
)

# İzahat generasiya edin
x_instance = X_norm[0]
explanation = explainer.explain_instance(x_instance)

# İzahatı göstərin
print(explainer.visualize_explanation(explanation))
```

### SHAP İzahatı

```python
from inference.explainers.shap_explainer import SHAPExplainer

# SHAP izahatçısını yaradın
explainer = SHAPExplainer(
    model=model,
    feature_names=[f"feature_{i}" for i in range(X_norm.shape[1])],
)

# İzahat generasiya edin
explanation = explainer.explain_instance(x_instance)

# İzahatı göstərin
print(explainer.visualize_explanation(explanation))
```

---

## 6. REST API İstifadəsi

### FastAPI ilə Model Deploy Etmək

```python
from inference.api.fastapi_app import run_api

# API-ni başladın
run_api(host="0.0.0.0", port=8000)
```

API-ya müraciət etmək üçün:
```python
import requests

url = "http://localhost:8000/predict"
data = {
    "model_name": "linear_regression",
    "data": [[1.0, 2.0, 3.0, 4.0, 5.0]],
}

response = requests.post(url, json=data)
result = response.json()
print(f"Prediction: {result['prediction']}")
```

---

## 7. CLI İstifadəsi

### Model Öyrətmək

```bash
python -m interfaces.cli.main_cli train --model linear_regression --data train.csv --target y
```

### Proqnozlaşdırmaq

```bash
python -m interfaces.cli.main_cli predict --model linear_regression --data test.csv
```

### Qiymətləndirmək

```bash
python -m interfaces.cli.main_cli evaluate --model linear_regression --data test.csv --target y
```

---

## Növbəti Addımlar

- [Quraşdırma](installation.md) — Layihəni quraşdırmaq
- [Arxitektura](architecture.md) — Layihənin arxitekturasını öyrənmək
- [Modullar](modules/) — Hər bir modulu detallı öyrənmək
- [API Sənədləri](api_reference.md) — REST API sənədləri
