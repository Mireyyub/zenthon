# Quraşdırma

Bu səhifədə **Zenthon AI System**-i quraşdırmaq üçün bütün addımlar təsvir edilmişdir.

---

## Tələb Olunanlar

- **Python 3.8+**
- **pip** (Python paket meneceri)
- **Git** (versiya idarəetmə sistemi)

---

## Quraşdırma Addımları

### 1. Repository-nu Klonlayın

```bash
cd /path/to/your/workspace
git clone https://github.com/Mireyyub/zenthon.git
cd zenthon
```

### 2. Virtual Environment Yaradın

**Tövsiyə olunur:** Layihəni izolyasiya etmək üçün virtual environment istifadə edin.

#### Linux/MacOS

```bash
python -m venv venv
source venv/bin/activate
```

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Asılılıqları Quraşdırın

Layihə üçün lazım olan bütün Python paketlərini quraşdırmaq üçün:

```bash
pip install --upgrade pip
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

PyTorch və CUDA dəstəyini yoxlamaq üçün:

```bash
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

**Gözlənilən çıxış:**
```
PyTorch version: 1.12.0+cu113
CUDA available: True
```

---

## Əlavə Quraşdırma Seçimləri

### GPU Dəstəyini Quraşdırmaq

Əgər siz **NVIDIA GPU**-dan istifadə edirsizsə, **CUDA** və **cuDNN** quraşdırılmalıdır.

#### CUDA Quraşdırma

1. **NVIDIA CUDA Toolkit**-i yukleyin:
   - [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)

2. **cuDNN**-i yukleyin:
   - [cuDNN](https://developer.nvidia.com/cudnn)

3. **PyTorch**-ü CUDA dəstəyilə quraşdırın:
   ```bash
   pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
   ```

### Development Üçün Quraşdırma

Əgər siz layihəni inkişaf etdirəcəksinizsə, əlavə asılılıqlar quraşdırın:

```bash
pip install black flake8 pylint isort pytest pytest-cov mkdocs mkdocs-material
```

---

## Müşkiləmi Var?

Əgər quraşdırma zamanı problemlər yaranarsa:

1. **Python versiyasını yoxlayın:**
   ```bash
   python --version
   ```

2. **pip versiyasını yoxlayın:**
   ```bash
   pip --version
   ```

3. **Asılılıqları yeniləyin:**
   ```bash
   pip install --upgrade numpy pandas scikit-learn torch
   ```

4. **GitHub Issues**-da sual verin:
   → [Mireyyub/zenthon/issues](https://github.com/Mireyyub/zenthon/issues)
