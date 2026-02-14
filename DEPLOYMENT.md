# 🚀 Guia de Deploy - MIP System

## Deploy no Streamlit Cloud

### Passo 1: Preparar o Repositório

Certifique-se de que todos os arquivos estão no GitHub:

```bash
git add .
git commit -m "Preparação para deploy cloud"
git push origin main
```

### Passo 2: Criar Conta no Streamlit Cloud

1. Acesse: https://cloud.streamlit.io/
2. Faça login com sua conta GitHub
3. Clique em "New app"

### Passo 3: Conectar o Repositório

1. Selecione o repositório: `techtrendsbr/app-rotina-mip`
2. Selecione a branch: `main`
3. Arquivo principal: `app.py`

### Passo 4: Configurar Secrets (CRUCIAL)

Na abas "Settings" → "Secrets", adicione:

**Nome do Secret:** `gcp_service_account`
**Valor:** (TODO o conteúdo JSON do seu Google Service Account)

```
{
  "type": "service_account",
  "project_id": "seu-projeto-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "...@...iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

**Para obter as credenciais:**
1. Abra seu arquivo `service_account.json`
2. Copie TODO o conteúdo
3. Cole no campo de valor do secret

### Passo 5: Deploy

Clique em "Deploy" e aguarde alguns seguntos.

Seu app estará disponível em:
`https://app-rotina-mip.streamlit.app/`

---

## 🔧 Troubleshooting Deploy

### Erro: "Module not found: gspread"
**Solução:** Verifique se `requirements.txt` está no repositório

### Erro: "Não foi possível encontrar credenciais"
**Solução:**
1. Verifique se o secret `gcp_service_account` foi adicionado
2. Verifique se o JSON está completo (sem aspas externas)
3. Verifique se o service account tem permissão na planilha

### Erro: "APIError: {
  "errors": [
    {
      "domain": "global",
      "reason": "forbidden"
    }
  ]
}"
**Solução:** O Service Account não tem acesso à planilha. Adicione o email do service account como editor na planilha "Journal Database".

### Verificar Logs
No Streamlit Cloud, vá em:
- Settings → Logs
- "Manage app" → "View logs"

---

## 📦 Dependências Cloud (requirements.txt)

O arquivo `requirements.txt` DEVE conter:

```
streamlit
pandas
plotly
gspread
oauth2client
python-dotenv
```

Certifique-se de que este arquivo está no commit!

---

## 🔄 CI/CD Automático (Opcional)

Para deploy automático a cada push no `main`, configure:

1. No Streamlit Cloud: Settings → Deploy settings
2. Enable "Automatic updates"
3. Selecione a branch `main`

Agora toda vez que você fizer `git push origin main`, o app será automaticamente atualizado!

---

## 🔐 Segurança no Cloud

**NUNCA** commitar:
- ❌ `service_account.json`
- ❌ `.streamlit/secrets.toml`
- ❌ Arquivos com credenciais reais

**Arquivos .gitignore DEVEM conter:**
```
service_account.json
service-account.json
.streamlit/secrets.toml
```

O Streamlit Cloud usa o sistema de Secrets separado por segurança!
