# Checklist de Deploy na Streamlit Cloud

## ✅ Status Atual: Pronto para Deploy

**Data**: 14/02/2026
**Commit**: 6816389
**Branch**: main
**Repo**: techtrendsbr/app-rotina-mip

---

## 📋 Checklist Pré-Deploy

### 1. Código e Versionamento ✅
- [x] Código completo desenvolvido (app.py, db_manager.py)
- [x] Sistema de autenticação robusto implementado
- [x] Parsing de dados com regex funcional
- [x] Visualizações interativas (Plotly)
- [ [x] ](https://github.com/techtrendsbr/app-rotina-mip) Repositório no GitHub
- [x] Commit mais recente: `6816389 - fix: corrigir config.toml e app.py para deploy em nuvem`
- [x] .gitignore configurado corretamente
- [x] requirements.txt com todas as dependências

### 2. Configuração Streamlit ✅
- [x] `.streamlit/config.toml` válido e otimizado
- [x] Logging habilitado (level = "info")
- [x] `gatherUsageStats = false` para evitar prompts
- [x] App testado localmente: http://localhost:8501 ✅

### 3. Google Sheets API ✅
- [x] db_manager.py com múltiplas estratégias de autenticação
- [x] Suporte a service_account.json (local)
- [x] Suporte a Streamlit Secrets (nuvem)
- [x] Logging robusto com st.write(), st.error(), st.success()
- [x] Tratamento de erros com mensagens claras

---

## 🚀 Passos para Deploy na Streamlit Cloud

### Passo 1: Acessar Streamlit Cloud
1. Acesse: https://cloud.streamlit.io/
2. Faça login com sua conta Google/GitHub
3. Clique em: **"New app"**

### Passo 2: Conectar Repositório
1. Selecione: **GitHub**
2. Busque por: `techtrendsbr/app-rotina-mip`
3. Selecione o branch: **main**
4. Arquivo principal: **app.py**
5. Clique em: **"Next"**

### Passo 3: Configurar Secrets (CRUCIAL!)
1. Na seção "Secrets", clique em: **"+ New secret"**
2. **Nome do secret**: `service_account_file_content`
3. **Valor do secret**:
   - Abra seu arquivo `service_account.json` local
   - Copie **TODO** o conteúdo JSON
   - Cole como texto (string) no campo de valor
   - Deve parecer algo como:
   ```json
   {
     "type": "service_account",
     "project_id": "seu-projeto",
     "private_key_id": "...",
     "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
     "client_email": "...",
     "client_id": "...",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token"
   }
   ```
4. Clique em: **"Save secret"**
5. Clique em: **"Deploy app"**

### Passo 4: Aguardar Deploy
- O deploy leva de 2-5 minutos na primeira vez
- Você verá logs de build em tempo real
- Aguarde mensagem: "Your app is live!"

### Passo 5: Verificar Deploy
1. Acesse a URL fornecida (ex: `https://app-rotina-mip.streamlit.app`)
2. Verifique se não há erros na interface
3. **IMPORTANTE**: Veja os logs de debug com `st.write()` aparecendo na interface

---

## 🔍 Verificações Pós-Deploy

### Testar Conexão Google Sheets
- [ ] App carrega sem erros de conexão
- [ ] Logs mostram: `✅ CONECTADO via Streamlit Secrets (JSON Payload)`
- [ ] Dados da planilha aparecem no dashboard
- [ ] Adicionar novo registro funciona
- [ ] Editar registros funciona
- [ ] Filtros de data funcionam

### Testar Parsing de Dados
- [ ] Teste com texto: "Dormi às 23h, acordei às 7h, treinei perna, me sinto produtivo!"
- [ ] Sono extraído: 8 horas
- [ ] Treino detectado: True (musculação)
- [ ] Sentimento calculado: 7/10

### Testar Visualizações
- [ ] Gráfico temporal aparece (Sono x Sentimento)
- [ ] Mapa de calor de treinos funciona
- [ ] Gráficos de hábitos (meditação, leitura, dieta) aparecem
- [ ] KPIs na sidebar atualizam com filtros

---

## 🐛 Troubleshooting Comum

### Erro: "Secret não encontrado"
**Sintoma**: App mostra `❌ Chave 'service_account_file_content' não encontrada em st.secrets`

**Solução**:
1. Volte em: https://cloud.streamlit.io/
2. Selecione seu app → **Settings** → **Secrets**
3. Adicione o secret com o nome EXATO: `service_account_file_content`
4. Cole o JSON completo como texto
5. Salve e re-deploy

### Erro: "Planilha não encontrada"
**Sintoma**: `APIError: 403 { "error": { "status": "PERMISSION_DENIED" } }`

**Solução**:
1. Abra sua planilha "Journal Database" no Google Sheets
2. Clique em: **Compartilhar**
3. Cole o email da service account (campo `client_email` do JSON)
4. Dê permissão: **Editor**
5. Salve e re-deploy

### Erro: "MalformedFraming"
**Sintoma**: Erro de parsing no gspread

**Solução**:
1. Verifique se o JSON está completo e válido
2. Não adicione caracteres de escape (o Streamlit lida com isso)
3. Certifique-se que o JSON inclui todos os campos obrigatórios
4. Use uma ferramenta de JSON validator para verificar

### Erro: "Module not found"
**Sintoma**: `ModuleNotFoundError: No module named 'gspread'`

**Solução**:
1. Verifique se `requirements.txt` está no repositório
2. Confirme que todas as dependências estão listadas
3. Re-deploy o app

---

## 📊 URLs Importantes

- **GitHub Repo**: https://github.com/techtrendsbr/app-rotina-mip
- **Streamlit Cloud**: https://cloud.streamlit.io/
- **URL App (pós-deploy)**: https://app-rotina-mip.streamlit.app

---

## 📝 Notas Importantes

### Sobre o JSON Payload
O app usa a estratégia de "JSON Payload" para os secrets:
- O secret deve conter o JSON COMPLETO como uma string
- Não quebre linhas manualmente
- Não adicione escape characters (`\\n` → `\n`)
- Copie direto do arquivo `service_account.json` local

### Sobre Logs na Nuvem
Os logs de debug usando `st.write()` aparecem:
1. Na interface do app (para o usuário ver)
2. Nos logs de deploy (em "Manage app" → "Deployment logs")
3. Use para troubleshooting de autenticação

### Sobre Compartilhamento da Planilha
A service account PRECISA ter acesso:
1. Email: `client_email` do JSON (ex: `meu-projeto@appspot.gserviceaccount.com`)
2. Permissão: **Editor**
3. Planilha: **"Journal Database"**

---

## ✨ Próximos Melhoramentos

Após o deploy inicial:
- [ ] Testar com dados reais
- [ ] Adicionar mais filtros de data
- [ ] Implementar exportação de relatórios
- [ ] Adicionar análise avançada com ML
- [ ] Implementar autenticação de usuários

---

**Status Final**: ✅ **PRONTO PARA DEPLOY**

Siga os passos acima e seu app estará na nuvem em menos de 10 minutos!
