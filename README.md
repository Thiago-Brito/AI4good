# AI4good

Este workspace junta duas partes do mesmo trabalho:

- `code/`: codigo dos experimentos, prototipos e aplicacoes.
- `academy/papers/`: relatorio tecnico e artigo cientifico.

A inspiracao vem do workspace do professor:
https://github.com/lsfcin/workspace

## Ideia principal

O workspace e uma pasta raiz que guarda o contexto do projeto. Em vez de deixar codigo,
referencias, resultados e texto final espalhados, cada coisa tem um lugar.

O principio pratico e simples: se algo importa para o trabalho, deve virar arquivo.
Assim outra pessoa, ou um agente de IA, consegue continuar sem depender da memoria de
uma conversa anterior.

## Estrutura

| Pasta | Uso |
| --- | --- |
| `code/rede-neural-do-zero/` | Projeto Python/Streamlit atual |
| `academy/papers/artigo-disciplina/` | Artigo/relatorio da disciplina |
| `academy/papers/artigo-overleaf/` | Repositorio clonado do Overleaf, com template LNCS/Springer |
| `academy/refs/` | Referencias gerais de pesquisa |
| `core/flows/research/` | Protocolos simples para pesquisa e escrita |
| `core/templates/` | Modelos de arquivos para novos trabalhos |
| `outputs/` | Saidas geradas localmente, como PDFs, figuras e logs |
| `tools/` | Scripts de verificacao e apoio |

## Como usar no dia a dia

Para rodar o codigo atual:

```powershell
cd code\rede-neural-do-zero
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app_conexoes.py
```

Para checar a organizacao do workspace:

```powershell
python tools\workspace_check.py
```

Para tentar compilar o artigo:

```powershell
python tools\compile_article.py
```

No momento, a sua maquina ainda nao tem `pdflatex`/`bibtex` no PATH. Por isso a
compilacao do PDF vai pedir uma instalacao de LaTeX, como MiKTeX ou TeX Live.

## Overleaf

O repositorio Overleaf foi clonado em:

```text
academy/papers/artigo-overleaf/
```

Ele e um repositorio Git separado, com remoto proprio:

```text
https://git@git.overleaf.com/6a920ba2c3f0c914aa7c7185
```

Nao salve token do Overleaf em arquivos do projeto. Use o token apenas quando o
Git pedir senha para `pull` ou `push`.

## Perguntas pendentes

As respostas devem ser registradas em `academy/papers/artigo-disciplina/PROJECT.md`.

1. Qual e o tema exato do artigo?
2. O professor pediu algum template especifico, como SBC, IEEE, ACM ou ABNT?
3. O trabalho sera individual ou em grupo?
4. O artigo precisa ser escrito em portugues, ingles ou ambos?
5. Quais entregas a disciplina exige: codigo, relatorio, apresentacao, repositorio Git?
