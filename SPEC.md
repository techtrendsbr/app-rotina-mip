# ESPECIFICAÇÃO DO PROJETO: MIP (Motor de Inteligência de Performance)

## 1. OBJETIVO
Desenvolver uma aplicação web em Python (Streamlit) que atue como um dashboard de performance pessoal. O app deve ler e escrever em uma planilha do Google Sheets que contém registros diários de rotina (Diário).

## 2. FONTE DE DADOS (Google Sheets)
A aplicação deve se conectar à API do Google Sheets.
Estrutura das colunas esperada:
- Coluna A: Data (Data do registro)
- Coluna B: Mensagem Crua (Texto narrativo transcrito de áudio)
- Coluna C: Resposta (Análise prévia da IA - Metadados)
- Colunas Futuras (Calculadas): O app deve ser capaz de interpretar o texto da Coluna B para extrair métricas.

## 3. REGRAS DE NEGÓCIO E PARSING (ETL)
O sistema deve processar o texto da "Mensagem Crua" para gerar visualizações.
Lógica de Extração (Regex/NLP Simples):
- **Sono:** Extrair horários de acordar/dormir e calcular horas totais.
- **Treino:** Identificar se houve treino (True/False) e tipo.
- **Sentimento:** Score calculado de 1-10 baseado na polaridade do texto.
- **Rotina:** Identificar keywords: Meditação, Leitura, Dieta.

## 4. FUNCIONALIDADES DO APP (Escopo)
### A. Barra Lateral (Sidebar)
- Filtro de Data (Início/Fim).
- Botões Presets: 7d, 30d, 90d, Ano.
- KPI Resumo: Média de sono do período, Frequência de treino %.

### B. Dashboard Principal
1. **Gráfico Temporal (Line Chart):** Eixo X=Data, Eixo Y1=Sono, Eixo Y2=Sentimento.
2. **Mapa de Calor (Calendar Heatmap):** Visualização de consistência (Dias com registro/treino).
3. **Comparativo (Delta):** Comparar médias do período selecionado vs. período anterior.
4. **Insight Textual:** Um box gerando um "Veredito" automático sobre os dados (ex: "Sua consistência caiu 20% no fds").

### C. Gestão de Dados (CRUD)
- **Visualização:** Tabela interativa (`st.data_editor`) mostrando os dados filtrados.
- **Edição:** Permitir editar o texto da célula e salvar de volta no Google Sheets.
- **Adição:** Formulário para inserir novo dia (Data + Texto) -> Append na planilha.
- **Deleção:** Botão para remover linhas.

## 5. STACK TÉCNICA
- Python 3.x
- Streamlit (Frontend)
- Pandas (Manipulação de Dados)
- Plotly (Gráficos Interativos)
- Gspread + OAuth2 (Conexão Google Sheets)
- Python-dotenv (Gestão de credenciais)

## 6. REQUISITOS DE IMPLEMENTAÇÃO
- O código deve ser modular.
- Tratamento de erro caso a conexão falhe.
- Uso de st.cache_data para evitar estourar limites da API do Google.