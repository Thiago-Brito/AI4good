# Enviar para o Google Slides

O botão **Google Slides** do editor (e o comando `slidedsl google-slides arquivo.pptx`) converte o
deck atual em uma apresentação do Google, editável, no seu Drive, e abre o link.

- Login do Google com confirmação (OAuth com PKCE), retorno local em `127.0.0.1`.
- Permissão mínima `drive.file`: o SlideDSL só enxerga os arquivos que ele mesmo criou.
- Sem dependência nova; credencial e token ficam em `config/` e são ignorados pelo Git.
- Para levar ao Canva: no Canva, *Uploads → Google Drive* (ou baixe o PPTX e importe).

## Configuração (uma vez, cerca de 5 minutos)

1. Abra <https://console.cloud.google.com/> e crie um projeto (ex.: "SlideDSL").
2. **APIs e serviços → Biblioteca** → procure **Google Drive API** → **Ativar**.
3. **Google Auth Platform** (tela de consentimento OAuth) → **Começar**:
   nome do app "SlideDSL", seu e-mail de suporte, público **Externo**, seu e-mail de contato → Criar.
4. **Público → Usuários de teste → Adicionar usuários**: o seu Gmail.
5. **Clientes → Criar cliente** → tipo **App para computador** → Criar → **Baixar JSON**.
6. Salve o arquivo baixado como `code/slidedsl/config/google_client_secret.json`
   (ou aponte `SLIDEDSL_GOOGLE_CLIENT_SECRET=` no `.env` para outro caminho).
7. Reinicie `slidedsl serve`.

## Uso

1. Abra um deck no editor e clique em **Google Slides**.
2. Na primeira vez, abre a tela do Google. Ela avisa "O Google não verificou este app" (normal
   para app em teste): clique em **Continuar** e **Permitir**.
3. A mesma aba passa a mostrar a apresentação convertida; o link também aparece na barra de status.

Pela linha de comando: `.venv\Scripts\slidedsl.exe google-slides outputs\sem2\demo_sem2_v4\apresentacao.pptx`.

## Limites conhecidos

- App em modo de teste: o Google expira a sessão em 7 dias; o SlideDSL pede o login de novo.
- A conversão é do próprio Google: fontes ausentes no Google Slides são trocadas por similares.
- Para desconectar: apague `config/google_token.json` e remova o acesso em
  <https://myaccount.google.com/permissions>.
