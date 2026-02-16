# COMTRADE Disturbance Analyzer

Projeto para análise de desligamentos/perturbações com base em sinais elétricos.

## Consigo rodar no terminal do Windows?

**Sim.** Você consegue rodar tanto no modo web quanto no modo offline.

### Pré-requisito

- Python 3.10+ instalado e disponível no `PATH`.

### Windows (PowerShell) — modo offline (recomendado sem internet)

```powershell
python .\offline_cli.py --csv .\exemplo.csv --voltage VA VB VC --current IA IB IC --line-km 120 --kv 230 --z1 0.38
```

### Windows (PowerShell) — modo web

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### Windows (CMD) — modo web

```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
streamlit run app.py
```

> Se estiver sem internet, use o modo offline (`offline_cli.py`) que não depende de bibliotecas externas.

---

## Opção 1 (Web): Streamlit + COMTRADE

Aplicativo web para leitura direta de arquivos COMTRADE (`.cfg` + `.dat`) com visualização e análise inicial.

### Funcionalidades (web)

- Upload de arquivos COMTRADE (`.cfg` e `.dat`).
- Extração de sinais analógicos.
- Cálculo de métricas elétricas (RMS, pico e componente DC aproximada).
- Detecção simples de sobretensão/subtensão e sobrecorrente.
- Estimativa de distância da falta por impedância aparente.
- Gráficos e resumo textual.

### Execução (web)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Opção 2 (Offline / sem internet): CLI em Python puro

Se você estiver sem internet ou sem conseguir instalar dependências, use o modo offline:

- Script: `offline_cli.py`
- Sem `numpy`, `pandas`, `streamlit`, `plotly` ou `comtrade`.
- Entrada: CSV com colunas de sinais (ex.: `time,VA,VB,VC,IA,IB,IC`).

### Execução (offline)

```bash
python offline_cli.py --csv exemplo.csv --voltage VA VB VC --current IA IB IC --line-km 120 --kv 230 --z1 0.38
```

---

## Testes

### Testes sem dependências externas

```bash
python -m unittest -q tests/test_basic_analysis.py
```

### Testes da camada com `numpy/pandas` (opcionais)

```bash
pytest -q tests/test_comtrade_analyzer.py
```
