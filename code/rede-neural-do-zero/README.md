# Rede Neural do Zero com Streamlit

Aplicacao didatica que implementa uma rede neural multicamada manualmente com
NumPy. Nao usa TensorFlow, PyTorch, Keras, scikit-learn nem biblioteca pronta
de redes neurais.

## Como executar

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Versao com as conexoes se formando:

```powershell
python -m streamlit run app_conexoes.py
```

## O que e exibido

- epoca atual, perda e acuracia;
- ativacoes dentro dos neuronios;
- conexoes positivas e negativas com espessura proporcional ao peso;
- evolucao das metricas;
- fronteira de decisao aprendida pela rede.

