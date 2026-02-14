import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import re
from db_manager import SheetManager

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="MIP - Motor de Inteligência de Performance",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# FUNÇÕES DE PARSING (ETL)
# ==========================================

def parse_sleep_data(text: str) -> float:
    """
    Extrai horas de sono do texto.
    Busca padrões como "dormi às 23h", "acordei às 7h", "8 horas de sono"
    """
    if pd.isna(text) or not isinstance(text, str):
        return 0.0

    # Padrões para horas de dormir e acordar
    sleep_patterns = {
        'dormir|dormi|sleep': r'(?:dormir|dormi|sleep)\s*(?:às|at)?\s*(\d{1,2})h?(\d{2})?',
        'acordar|acordei|wake': r'(?:acordar|acordei|wake)\s*(?:às|at)?\s*(\d{1,2})h?(\d{2})?',
    }

    hours_found = []

    for keyword, pattern in sleep_patterns.items():
        matches = re.finditer(pattern, text.lower())
        for match in matches:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            hours_found.append(hour + minute / 60)

    # Se encontrou dormir e acordar, calcular diferença
    if len(hours_found) >= 2:
        sleep_time = hours_found[0]
        wake_time = hours_found[1]

        if wake_time < sleep_time:
            wake_time += 24  # Ajustar para próximo dia

        total_sleep = wake_time - sleep_time
        return round(total_sleep, 2)

    # Buscar menção direta de horas
    direct_match = re.search(r'(\d+(?:\.\d+)?)\s*horas?\s*de\s*sono', text.lower())
    if direct_match:
        return float(direct_match.group(1))

    return 0.0


def parse_workout(text: str) -> tuple:
    """
    Identifica se houve treino e o tipo.
    Retorna (bool, str)
    """
    if pd.isna(text) or not isinstance(text, str):
        return (False, "")

    text_lower = text.lower()

    workout_keywords = [
        'treinei', 'treino', 'workout', 'malhei', 'academia',
        'corri', 'corrida', 'musculação', 'musculacao', 'exercício',
        'exercicio', 'natação', 'natacao', 'bike', 'ciclismo'
    ]

    has_workout = any(keyword in text_lower for keyword in workout_keywords)

    # Identificar tipo de treino
    workout_types = {
        'musculação': ['musculação', 'musculacao', 'peso', 'força'],
        'cardio': ['corri', 'corrida', 'cardio', 'bike', 'ciclismo', 'natação', 'natacao'],
        'funcional': ['funcional', 'crossfit', 'hiit']
    }

    workout_type = ""
    if has_workout:
        for w_type, keywords in workout_types.items():
            if any(keyword in text_lower for keyword in keywords):
                workout_type = w_type
                break

        if not workout_type:
            workout_type = "geral"

    return (has_workout, workout_type)


def calculate_sentiment(text: str) -> int:
    """
    Calcula sentimento baseado em palavras-chave positivas/negativas.
    Retorna score de 1-10
    """
    if pd.isna(text) or not isinstance(text, str):
        return 5

    text_lower = text.lower()

    positive_words = [
        'bom', 'ótimo', 'otimo', 'excelente', 'feliz', 'produtivo',
        'energético', 'energetico', 'motivado', 'foco', 'consegui',
        'realizei', 'completei', 'sucesso', 'melhor', 'bem'
    ]

    negative_words = [
        'ruim', 'péssimo', 'pessimo', 'cansado', 'triste', 'estressado',
        'estressado', 'sem energia', 'fracasso', 'erro', 'difícil',
        'dificil', 'problema', 'preocupação', 'preocupacao', 'ansioso'
    ]

    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    # Calcular score base (1-10)
    base_score = 5
    sentiment = base_score + (positive_count * 0.5) - (negative_count * 0.5)

    return max(1, min(10, round(sentiment)))


def parse_routine_keywords(text: str) -> dict:
    """
    Identifica palavras-chave de rotina.
    Retorna dict com flags para cada hábito
    """
    if pd.isna(text) or not isinstance(text, str):
        return {'meditacao': False, 'leitura': False, 'dieta': False}

    text_lower = text.lower()

    keywords = {
        'meditacao': ['meditei', 'meditação', 'meditacao', 'mindfulness'],
        'leitura': ['li', 'livro', 'leitura', 'li livro', 'estudei'],
        'dieta': ['dieta', 'saudável', 'saudavel', 'comida saudável', 'jejum']
    }

    result = {}
    for key, words in keywords.items():
        result[key] = any(word in text_lower for word in words)

    return result


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica todas as funções de parsing para criar colunas derivadas.
    """
    if df.empty:
        return df

    # Criar cópia para evitar SettingWithCopyWarning
    df_processed = df.copy()

    # Aplicar parsing
    df_processed['Sono (horas)'] = df_processed['Mensagem Crua'].apply(parse_sleep_data)
    df_processed['Treino'] = df_processed['Mensagem Crua'].apply(lambda x: parse_workout(x)[0])
    df_processed['Tipo Treino'] = df_processed['Mensagem Crua'].apply(lambda x: parse_workout(x)[1])
    df_processed['Sentimento (1-10)'] = df_processed['Mensagem Crua'].apply(calculate_sentiment)

    # Extrair keywords de rotina
    routine_data = df_processed['Mensagem Crua'].apply(parse_routine_keywords)
    df_processed['Meditação'] = routine_data.apply(lambda x: x['meditacao'])
    df_processed['Leitura'] = routine_data.apply(lambda x: x['leitura'])
    df_processed['Dieta'] = routine_data.apply(lambda x: x['dieta'])

    # Tentar converter coluna Data para datetime
    try:
        df_processed['Data'] = pd.to_datetime(df_processed['Data'], dayfirst=True, errors='coerce')
    except:
        pass

    # Ordenar por data
    df_processed = df_processed.sort_values('Data', ascending=False)

    return df_processed


# ==========================================
# FUNÇÕES DE VISUALIZAÇÃO
# ==========================================

def create_temporal_chart(df: pd.DataFrame):
    """Gráfico temporal com Sono e Sentimento."""
    if df.empty or 'Sono (horas)' not in df.columns:
        return None

    df_sorted = df.sort_values('Data')

    fig = go.Figure()

    # Adicionar linha de sono
    fig.add_trace(go.Scatter(
        x=df_sorted['Data'],
        y=df_sorted['Sono (horas)'],
        mode='lines+markers',
        name='Sono (horas)',
        line=dict(color='#3498db', width=2),
        yaxis='y'
    ))

    # Adicionar linha de sentimento
    fig.add_trace(go.Scatter(
        x=df_sorted['Data'],
        y=df_sorted['Sentimento (1-10)'],
        mode='lines+markers',
        name='Sentimento (1-10)',
        line=dict(color='#e74c3c', width=2),
        yaxis='y2'
    ))

    fig.update_layout(
        title='📈 Evolução Temporal: Sono x Sentimento',
        xaxis_title='Data',
        yaxis=dict(
            title='Sono (horas)',
            titlefont=dict(color='#3498db'),
            tickfont=dict(color='#3498db')
        ),
        yaxis2=dict(
            title='Sentimento (1-10)',
            titlefont=dict(color='#e74c3c'),
            tickfont=dict(color='#e74c3c'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )

    return fig


def create_workout_heatmap(df: pd.DataFrame):
    """Mapa de calor de treinos."""
    if df.empty or 'Data' not in df.columns:
        return None

    # Garantir que temos coluna de data
    df_temp = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_temp['Data']):
        df_temp['Data'] = pd.to_datetime(df_temp['Data'], errors='coerce')

    df_temp['Dia'] = df_temp['Data'].dt.day_name()
    df_temp['Semana'] = df_temp['Data'].dt.isocalendar().week

    # Criar pivot table
    pivot = df_temp.pivot_table(
        values='Treino',
        index='Dia',
        columns='Semana',
        aggfunc='sum',
        fill_value=0
    )

    # Ordenar dias da semana
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = pivot.reindex(day_order, fill_value=0)

    fig = px.imshow(
        pivot,
        labels=dict(x="Semana", y="Dia da Semana", color="Treinos"),
        color_continuous_scale='Viridis',
        title='🔥 Mapa de Calor: Consistência de Treinos'
    )

    fig.update_layout(height=400, template='plotly_white')

    return fig


def calculate_kpis(df: pd.DataFrame) -> dict:
    """Calcula KPIs do período."""
    if df.empty:
        return {
            'avg_sleep': 0,
            'workout_freq': 0,
            'avg_sentiment': 0,
            'total_days': 0
        }

    return {
        'avg_sleep': round(df['Sono (horas)'].mean(), 1),
        'workout_freq': round(df['Treino'].mean() * 100, 1),
        'avg_sentiment': round(df['Sentimento (1-10)'].mean(), 1),
        'total_days': len(df)
    }


def generate_insight(df: pd.DataFrame, kpis: dict) -> str:
    """Gera insight textual sobre os dados."""
    if df.empty:
        return "📊 Sem dados suficientes para análise."

    insights = []

    # Sono
    if kpis['avg_sleep'] >= 7:
        insights.append(f"😴 **Sono:** Excelente! Média de {kpis['avg_sleep']}h/dia")
    elif kpis['avg_sleep'] >= 6:
        insights.append(f"😴 **Sono:** Aceitável, mas pode melhorar ({kpis['avg_sleep']}h/dia)")
    else:
        insights.append(f"⚠️ **Sono:** Atenção! Média baixa de {kpis['avg_sleep']}h/dia")

    # Treino
    if kpis['workout_freq'] >= 70:
        insights.append(f"💪 **Treino:** Ótima consistência ({kpis['workout_freq']}% dos dias)")
    elif kpis['workout_freq'] >= 50:
        insights.append(f"💪 **Treino:** Frequência moderada ({kpis['workout_freq']}% dos dias)")
    else:
        insights.append(f"📌 **Treino:** Tente aumentar a frequência ({kpis['workout_freq']}% dos dias)")

    # Sentimento
    if kpis['avg_sentiment'] >= 7:
        insights.append(f"😊 **Humor:** Positivo ({kpis['avg_sentiment']}/10)")
    elif kpis['avg_sentiment'] <= 4:
        insights.append(f"😔 **Humor:** Precisa de atenção ({kpis['avg_sentiment']}/10)")

    return "\n\n".join(insights)


# ==========================================
# INTERFACE STREAMLIT
# ==========================================

def main():
    st.title("📊 MIP - Motor de Inteligência de Performance")
    st.markdown("---")

    # Inicializar SheetManager
    try:
        if 'db' not in st.session_state:
            st.session_state.db = SheetManager()

        # Exibir informações de conexão (expander por padrão fechado)
        with st.expander("🔧 Informações de Conexão (Debug)"):
            conn_info = st.session_state.db.get_connection_info()
            st.json(conn_info)

            st.caption(f"""
            **Ambiente Cloud (Streamlit Cloud):** Adicione `gcp_service_account` em st.secrets

            **Ambiente Local:** Use `service_account.json` ou `service-account.json`

            **Planilha:** `{conn_info['sheet_name']}`
            """)

    except Exception as e:
        st.error(f"❌ Erro ao conectar ao Google Sheets: {str(e)}")
        st.info("💡 Verifique se o arquivo `service_account.json` está correto e se a planilha 'Journal Database' existe.")
        st.info("📌 **Deploy Cloud:** Configure `st.secrets['gcp_service_account']` no Streamlit Cloud")
        return

    # Carregar dados com cache
    @st.cache_data(ttl=300)  # Cache de 5 minutos
    def load_data():
        return st.session_state.db.get_data()

    try:
        raw_df = load_data()
        df = process_data(raw_df)

        if df.empty:
            st.warning("⚠️ A planilha está vazia. Adicione seu primeiro registro!")
            df = pd.DataFrame(columns=['Data', 'Mensagem Crua', 'Resposta'])
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return

    # ==========================================
    # SIDEBAR - FILTROS
    # ==========================================
    st.sidebar.header("🔍 Filtros")

    # Filtro de data
    if not df.empty and 'Data' in df.columns:
        min_date = df['Data'].min()
        max_date = df['Data'].max()

        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Data Início", value=min_date)
        with col2:
            end_date = st.date_input("Data Fim", value=max_date)

        # Presets
        st.sidebar.markdown("**Presets Rápidos:**")
        preset_col1, preset_col2 = st.sidebar.columns(2)

        with preset_col1:
            if st.button("7d"):
                start_date = (max_date - timedelta(days=7)).date()
                end_date = max_date.date()
                st.rerun()

        with preset_col2:
            if st.button("30d"):
                start_date = (max_date - timedelta(days=30)).date()
                end_date = max_date.date()
                st.rerun()

        # Aplicar filtro
        df_filtered = df[
            (pd.to_datetime(df['Data']) >= pd.to_datetime(start_date)) &
            (pd.to_datetime(df['Data']) <= pd.to_datetime(end_date))
        ]
    else:
        df_filtered = df

    # KPIs na Sidebar
    st.sidebar.markdown("---")
    st.sidebar.header("📌 KPIs do Período")

    kpis = calculate_kpis(df_filtered)

    st.sidebar.metric("📅 Dias Analisados", kpis['total_days'])
    st.sidebar.metric("😴 Sono Médio", f"{kpis['avg_sleep']}h")
    st.sidebar.metric("💪 Frequência Treino", f"{kpis['workout_freq']}%")
    st.sidebar.metric("😊 Sentimento Médio", f"{kpis['avg_sentiment']}/10")

    # Insight
    st.sidebar.markdown("---")
    st.sidebar.markdown("💡 **Insight do Período:**")
    st.sidebar.markdown(generate_insight(df_filtered, kpis))

    # ==========================================
    # ABA PRINCIPAL
    # ==========================================
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Editor", "➕ Adicionar Novo"])

    # ==========================================
    # TAB 1: DASHBOARD
    # ==========================================
    with tab1:
        if df_filtered.empty:
            st.info("📊 Sem dados para exibir no período selecionado.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                fig_temporal = create_temporal_chart(df_filtered)
                if fig_temporal:
                    st.plotly_chart(fig_temporal, use_container_width=True)

            with col2:
                fig_heatmap = create_workout_heatmap(df_filtered)
                if fig_heatmap:
                    st.plotly_chart(fig_heatmap, use_container_width=True)

            # Gráficos de rosca para hábitos
            col3, col4, col5 = st.columns(3)

            with col3:
                if df_filtered['Meditação'].sum() > 0:
                    fig_meditation = px.pie(
                        values=[df_filtered['Meditação'].sum(), len(df_filtered) - df_filtered['Meditação'].sum()],
                        names=['Sim', 'Não'],
                        title='🧘 Meditação',
                        hole=0.6
                    )
                    st.plotly_chart(fig_meditation, use_container_width=True)

            with col4:
                if df_filtered['Leitura'].sum() > 0:
                    fig_reading = px.pie(
                        values=[df_filtered['Leitura'].sum(), len(df_filtered) - df_filtered['Leitura'].sum()],
                        names=['Sim', 'Não'],
                        title='📚 Leitura',
                        hole=0.6
                    )
                    st.plotly_chart(fig_reading, use_container_width=True)

            with col5:
                if df_filtered['Dieta'].sum() > 0:
                    fig_diet = px.pie(
                        values=[df_filtered['Dieta'].sum(), len(df_filtered) - df_filtered['Dieta'].sum()],
                        names=['Sim', 'Não'],
                        title='🥗 Dieta Saudável',
                        hole=0.6
                    )
                    st.plotly_chart(fig_diet, use_container_width=True)

    # ==========================================
    # TAB 2: EDITOR
    # ==========================================
    with tab2:
        st.subheader("📝 Editor de Registros")

        if df_filtered.empty:
            st.info("📊 Sem dados para editar.")
        else:
            # Mostrar dataframe editável
            df_display = df_filtered[['Data', 'Mensagem Crua', 'Resposta']].copy()

            # Converter data para formato de exibição
            df_display['Data'] = pd.to_datetime(df_display['Data']).dt.strftime('%d/%m/%Y')

            edited_df = st.data_editor(
                df_display,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True
            )

            # Botão para salvar alterações
            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Salvar Alterações", type="primary"):
                    st.success("✅ Alterações salvas na planilha!")
                    st.info("💡 Nota: A sincronização com o Google Sheets será implementada na próxima versão.")

            with col2:
                if st.button("🗑️ Deletar Linhas Selecionadas"):
                    st.warning("⚠️ Funcionalidade de deleção será implementada na próxima versão.")

    # ==========================================
    # TAB 3: ADICIONAR NOVO
    # ==========================================
    with tab3:
        st.subheader("➕ Adicionar Novo Registro")

        col1, col2 = st.columns(2)

        with col1:
            new_date = st.date_input("Data", value=datetime.now().date())

        with col2:
            st.write("")  # Spacer
            st.write(f"**Data Selecionada:** {new_date.strftime('%d/%m/%Y')}")

        new_text = st.text_area(
            "📝 Mensagem (Texto Narrativo)",
            placeholder="Ex: Hoje acordei às 7h, dormi bem. Treinei perna e me sinto produtivo...",
            height=150
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("➕ Adicionar Registro", type="primary", use_container_width=True):
                if new_text.strip():
                    try:
                        date_str = new_date.strftime('%d/%m/%Y')
                        st.session_state.db.append_data(date_str, new_text)
                        st.success(f"✅ Registro adicionado: {date_str}")
                        st.cache_data.clear()  # Limpar cache
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar: {str(e)}")
                else:
                    st.warning("⚠️ Por favor, insira uma mensagem.")

        with col2:
            if st.button("🔄 Limpar Campos", use_container_width=True):
                st.rerun()

        # Preview do parsing
        if new_text:
            st.markdown("---")
            st.markdown("### 👁️ Preview do Parsing")

            preview_data = {
                'Data': new_date.strftime('%d/%m/%Y'),
                'Sono (horas)': parse_sleep_data(new_text),
                'Treino': parse_workout(new_text)[0],
                'Tipo Treino': parse_workout(new_text)[1],
                'Sentimento (1-10)': calculate_sentiment(new_text)
            }

            routine_preview = parse_routine_keywords(new_text)
            preview_data.update(routine_preview)

            st.json(preview_data)


if __name__ == "__main__":
    main()
