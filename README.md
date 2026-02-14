# MIP - Motor de Inteligência de Performance

Aplicação web em Python (Streamlit) para dashboard de performance pessoal com integração ao Google Sheets.

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Conta Google com planilha "Journal Database"
- Arquivo `service_account.json` com credenciais do Google Service Account

## 🚀 Instalação e Execução

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Credenciais

Certifique-se de que o arquivo `service_account.json` está na raiz do projeto.

### 3. Executar Aplicação

```bash
streamlit run app.py
```

A aplicação estará disponível em: `http://localhost:8501`

---

## ☁️ Deploy na Nuvem (Streamlit Cloud)

Para fazer deploy no Streamlit Cloud, siga o guia completo:

📖 **[DEPLOYMENT.md](./DEPLOYMENT.md)**

**Resumo Rápido:**

1. **Fazer push do código** (já está no GitHub: `techtrendsbr/app-rotina-mip`)

2. **Conectar no Streamlit Cloud:**
   - Acesse: https://cloud.streamlit.io/
   - New app → Conectar repositório GitHub

3. **Configurar Secrets:**
   - Settings → Secrets
   - Adicionar: `gcp_service_account`
   - Valor: TODO o JSON do seu Google Service Account

4. **Deploy!**

👉 **URL Cloud:** https://cloud.streamlit.io/

---

## 📊 Funcionalidades

### Dashboard Principal
- **Gráfico Temporal**: Evolução de Sono x Sentimento
- **Mapa de Calor**: Consistência de treinos por dia da semana
- **KPIs**: Média de sono, frequência de treino, sentimento médio
- **Insights Automáticos**: Análise textual dos dados do período

### Parsing de Dados (ETL)

A aplicação extrai automaticamente informações do texto narrativo:

- **Sono**: Identifica horários de dormir/acordar e calcula total de horas
- **Treino**: Detecta se houve treino e o tipo (musculação, cardio, funcional)
- **Sentimento**: Score de 1-10 baseado em palavras-chave positivas/negativas
- **Hábitos**: Meditação, Leitura, Dieta saudável

### Editor de Dados

- Visualização tabular interativa
- Edição inline de registros
- Adição de novos registros
- Preview do parsing antes de salvar

## 🔧 Estrutura do Código

- `app.py`: Interface Streamlit e lógica de parsing
- `db_manager.py`: Classe `SheetManager` para conexão com Google Sheets
- `requirements.txt`: Dependências Python
- `service_account.json`: Credenciais do Google (não commitar)

## 📝 Estrutura da Planilha Google Sheets

A planilha deve ter 3 colunas:

| Coluna A | Coluna B | Coluna C |
|----------|----------|----------|
| Data | Mensagem Crua | Resposta |

Exemplo de formato de data: `14/02/2026` ou `14/02/26`

## 🎯 Filtros e Presets

- **Filtro de Data**: Selecionar período personalizado
- **Presets**: 7d, 30d, 90d, Ano
- **KPIs Dinâmicos**: Atualizados conforme período selecionado

## ⚠️ Tratamento de Erros

- Planilha vazia: Retorna DataFrame vazio com colunas padrão
- Datas incorretas: Usa `errors='coerce'` do pandas
- Falha de conexão: Mensagem de erro com instruções
- Parsing falha: Retorna valores padrão (0, False, 5)

## 📈 Exemplos de Parsing

### Exemplo 1:
```
"Hoje acordei às 7h, dormi às 23h. Treinei perna e me sinto produtivo!"
```
**Parse:**
- Sono: 8 horas
- Treino: True (musculação)
- Sentimento: 7/10

### Exemplo 2:
```
"Dormi mal, apenas 5 horas. Muito cansado hoje."
```
**Parse:**
- Sono: 5 horas
- Treino: False
- Sentimento: 3/10

## 🔐 Segurança

**IMPORTANTE**: Nunca commitar o arquivo `service_account.json` no versionamento.

Adicione ao `.gitignore`:
```
service_account.json
.DS_Store
__pycache__/
*.pyc
```

## 🛠️ Troubleshooting

### Erro: "Erro ao conectar ao Google Sheets"
- Verifique se o arquivo `service_account.json` está correto
- Confirme que a planilha "Journal Database" existe no Google Drive
- Verifique as permissões do Service Account na planilha

### Erro: "Planilha vazia"
- Adicione o primeiro registro através da aba "Adicionar Novo"
- Ou adicione manualmente no Google Sheets

### Parsing não funciona
- Verifique se o texto segue os padrões esperados
- Use o "Preview do Parsing" antes de salvar
- Ajuste os regex no código se necessário

## 📦 Dependências

- streamlit: Frontend web
- pandas: Manipulação de dados
- plotly: Gráficos interativos
- gspread: API Google Sheets
- oauth2client: Autenticação Google

## 🚀 Próximos Melhoramentos

- [ ] Sincronização bidirecional completa com Google Sheets
- [ ] Exportação de relatórios em PDF
- [ ] Machine Learning para análise de sentimento mais avançada
- [ ] Gráficos adicionais (comparativo por períodos)
- [ ] Autenticação de usuários
- [ ] Multi-idioma

## 📄 Licença

Uso pessoal e educacional.
