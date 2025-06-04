import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, time
import numpy as np
import base64
from io import BytesIO
import plotly.io as pio

# Importar utilitários (se arquivo existir)
try:
    from dashboard_utils import (
        load_css, 
        get_unique_chart_key, 
        limpar_nome,
        create_metric_card,
        create_alert_box,
        create_header,
        create_feature_card,
        DASHBOARD_CONFIG,
        REQUIRED_COLUMNS,
        CHART_COLORS
    )
except ImportError:
    # Fallback se arquivo de utilitários não existir
    def load_css(file_path="styles.css"):
        default_css = """
        .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 1rem; }
        .metric-value { font-size: 2.5rem; font-weight: bold; margin-bottom: 0.5rem; }
        .metric-label { font-size: 1rem; opacity: 0.9; }
        .success-box { background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%); padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0; }
        .warning-box { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0; }
        .info-box { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1rem; border-radius: 10px; color: white; margin: 1rem 0; }
        """
        st.markdown(f"<style>{default_css}</style>", unsafe_allow_html=True)
    
    def get_unique_chart_key(base_name):
        if 'chart_counter' not in st.session_state:
            st.session_state.chart_counter = 0
        st.session_state.chart_counter += 1
        return f"{base_name}_{st.session_state.chart_counter}"
    
    def limpar_nome(nome):
        if pd.isna(nome):
            return nome
        nome = str(nome).strip()
        nome = ' '.join(nome.split())
        nome = nome.title()
        nome = nome.replace(' Da ', ' da ').replace(' De ', ' de ').replace(' Do ', ' do ')
        nome = nome.replace(' Das ', ' das ').replace(' Dos ', ' dos ')
        return nome
    
    def create_metric_card(value, label):
        return f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>'
    
    def create_alert_box(message, box_type="info"):
        return f'<div class="{box_type}-box">{message}</div>'
    
    def create_header(title, subtitle=""):
        subtitle_html = f'<h3>{subtitle}</h3>' if subtitle else ''
        return f'<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; text-align: center; margin-bottom: 2rem; color: white;"><h1>{title}</h1>{subtitle_html}</div>'
    
    def create_feature_card(title, description, card_type="blue"):
        colors = {"blue": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "pink": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", "cyan": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"}
        return f'<div style="background: {colors.get(card_type, colors["blue"])}; padding: 2rem; border-radius: 15px; color: white; text-align: center; margin: 1rem 0;"><h3>{title}</h3><p>{description}</p></div>'
    
    DASHBOARD_CONFIG = {'page_title': "Dashboard Interativo - Frequência", 'page_icon': "🎓", 'layout': "wide", 'initial_sidebar_state': "expanded"}
    REQUIRED_COLUMNS = ['Data/hora', 'Nome', 'COMO CONHECEU O GRUPO?', 'PRIMEIRA VEZ NO GRUPO?', 'DDD+TELEFONE (SEM ESPAÇO)']
    CHART_COLORS = {'gradient_colors': ['#FF6B6B', '#FFE66D', '#4ECDC4', '#45B7D1']}

# Configuração da página
st.set_page_config(**DASHBOARD_CONFIG)

# Carregar CSS externo
load_css("styles.css")

# Header interativo
st.markdown(create_header(
    "🎓 Dashboard Interativo", 
    "Análise de Frequência de Alunos"
), unsafe_allow_html=True)

# Tabs principais para navegação
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visão Geral", 
    "🔍 Análise Detalhada", 
    "👥 Busca por Alunos", 
    "📈 Relatórios",
    "🧹 Qualidade dos Dados"
])

# Sidebar interativa
with st.sidebar:
    st.markdown("""
    <div style="background: rgba(255,255,255,0.1); padding: 1rem; 
                border-radius: 10px; margin-bottom: 1rem;">
        <h2 style="color: white; text-align: center;">⚙️ Controles</h2>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "📁 Escolha o arquivo CSV",
        type=['csv'],
        help="Faça upload do arquivo CSV com os dados de frequência"
    )

if uploaded_file is not None:
    try:
        # Verificar se o arquivo não está vazio
        if uploaded_file.size == 0:
            st.error("❌ O arquivo está vazio. Por favor, faça upload de um arquivo CSV válido.")
            st.stop()
        
        # Ler o arquivo com diferentes encodings
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1')
                st.info("ℹ️ Arquivo lido com encoding latin-1")
            except UnicodeDecodeError:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='cp1252')
                    st.info("ℹ️ Arquivo lido com encoding cp1252")
                except:
                    st.error("❌ Erro de encoding. Tente salvar o arquivo como CSV UTF-8.")
                    st.stop()
        except pd.errors.EmptyDataError:
            st.error("❌ O arquivo CSV está vazio ou mal formatado.")
            st.stop()
        except pd.errors.ParserError as e:
            st.error(f"❌ Erro ao analisar o arquivo CSV: {str(e)}")
            st.stop()
        
        # Verificar se o DataFrame foi criado e não está vazio
        if df is None or df.empty:
            st.error("❌ O arquivo não contém dados válidos.")
            st.stop()
        
        # Verificando colunas obrigatórias
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        
        if missing_columns:
            st.error(f"❌ Colunas obrigatórias ausentes: {missing_columns}")
            st.stop()
        
        # Processamento dos dados
        df['Data/hora'] = pd.to_datetime(df['Data/hora'], errors='coerce')
        df['Data'] = df['Data/hora'].dt.date
        df['Hora'] = df['Data/hora'].dt.time
        df['Hora_decimal'] = df['Data/hora'].dt.hour + df['Data/hora'].dt.minute/60
        df = df.dropna(subset=['Data/hora'])
        
        # Limpeza de nomes
        df['Nome_Original'] = df['Nome'].copy()
        df['Nome'] = df['Nome'].apply(limpar_nome)
        
        # Inicializar session state
        if 'df_corrigido' not in st.session_state:
            st.session_state.df_corrigido = df.copy()
        
        # Usar dados corrigidos
        df_working = st.session_state.df_corrigido.copy()
        
        # Sidebar - Filtros interativos
        with st.sidebar:
            st.markdown("### 🔍 Filtros Avançados")
            
            # Filtro de período
            if not df_working.empty:
                min_date = df_working['Data'].min()
                max_date = df_working['Data'].max()
                
                date_range = st.date_input(
                    "📅 Período:",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    df_filtered = df_working[(df_working['Data'] >= start_date) & (df_working['Data'] <= end_date)]
                else:
                    df_filtered = df_working
            else:
                df_filtered = df_working
            
            # Filtro por aluno
            alunos = sorted(df_filtered['Nome'].unique())
            selected_alunos = st.multiselect(
                "👥 Selecionar Alunos:",
                options=alunos,
                default=alunos
            )
            
            if selected_alunos:
                df_filtered = df_filtered[df_filtered['Nome'].isin(selected_alunos)]
            
            # Métricas em tempo real
            total_presencas = len(df_filtered)
            total_alunos = df_filtered['Nome'].nunique()
            total_dias = df_filtered['Data'].nunique()
            media_presencas = total_presencas / total_dias if total_dias > 0 else 0
            
            st.markdown("### 📊 Métricas Rápidas")
            st.metric("📈 Presenças", total_presencas)
            st.metric("👥 Alunos", total_alunos)
            st.metric("📅 Dias", total_dias)
            st.metric("⚡ Média/Dia", f"{media_presencas:.1f}")

        # TAB 1: VISÃO GERAL
        with tab1:
            st.markdown('<div class="animated-content">', unsafe_allow_html=True)
            
            # Cards de métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(create_metric_card(total_presencas, "Total de Presenças"), unsafe_allow_html=True)
            
            with col2:
                st.markdown(create_metric_card(total_alunos, "Total de Alunos"), unsafe_allow_html=True)
            
            with col3:
                st.markdown(create_metric_card(total_dias, "Dias de Aula"), unsafe_allow_html=True)
            
            with col4:
                st.markdown(create_metric_card(f"{media_presencas:.1f}", "Média Presenças/Dia"), unsafe_allow_html=True)
            
            # Gráficos interativos lado a lado
            col1, col2 = st.columns(2)
            
            with col1:
                # Top 15 alunos
                presencas_por_aluno = df_filtered.groupby('Nome').size().reset_index(name='Presenças')
                presencas_por_aluno = presencas_por_aluno.sort_values('Presenças', ascending=False)
                
                if total_dias > 0:
                    presencas_por_aluno['Frequência (%)'] = (presencas_por_aluno['Presenças'] / total_dias * 100).round(1)
                else:
                    presencas_por_aluno['Frequência (%)'] = 0
                
                fig_top = px.bar(
                    presencas_por_aluno.head(15),
                    x='Presenças',
                    y='Nome',
                    orientation='h',
                    title="🏆 Top 15 Alunos Mais Assíduos",
                    color='Frequência (%)',
                    color_continuous_scale='Viridis',
                    text='Presenças'
                )
                fig_top.update_layout(
                    height=500,
                    showlegend=False,
                    title_font_size=16,
                    font=dict(size=12)
                )
                fig_top.update_traces(textposition='outside')
                st.plotly_chart(fig_top, use_container_width=True, key=get_unique_chart_key("top_alunos"))
            
            with col2:
                # Distribuição por faixa de frequência
                if total_dias > 0:
                    freq_ranges = ['0-25%', '26-50%', '51-75%', '76-100%']
                    freq_counts = [
                        len(presencas_por_aluno[(presencas_por_aluno['Frequência (%)'] >= 0) & (presencas_por_aluno['Frequência (%)'] <= 25)]),
                        len(presencas_por_aluno[(presencas_por_aluno['Frequência (%)'] > 25) & (presencas_por_aluno['Frequência (%)'] <= 50)]),
                        len(presencas_por_aluno[(presencas_por_aluno['Frequência (%)'] > 50) & (presencas_por_aluno['Frequência (%)'] <= 75)]),
                        len(presencas_por_aluno[(presencas_por_aluno['Frequência (%)'] > 75) & (presencas_por_aluno['Frequência (%)'] <= 100)])
                    ]
                    
                    colors = CHART_COLORS['gradient_colors']
                    
                    fig_pie = px.pie(
                        values=freq_counts,
                        names=freq_ranges,
                        title="📊 Distribuição por Faixa de Frequência",
                        color_discrete_sequence=colors
                    )
                    fig_pie.update_layout(
                        height=500,
                        title_font_size=16,
                        font=dict(size=12)
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True, key=get_unique_chart_key("distribuicao_frequencia"))
            
            # Gráfico de evolução temporal
            st.subheader("📈 Evolução das Presenças ao Longo do Tempo")
            
            presencas_por_data = df_filtered.groupby('Data').size().reset_index(name='Presenças')
            
            fig_timeline = px.area(
                presencas_por_data,
                x='Data',
                y='Presenças',
                title="Tendência de Presenças",
                color_discrete_sequence=['#667eea']
            )
            fig_timeline.update_layout(
                height=400,
                showlegend=False,
                title_font_size=16
            )
            st.plotly_chart(fig_timeline, use_container_width=True, key=get_unique_chart_key("evolucao_temporal"))
            
            st.markdown("</div>", unsafe_allow_html=True)

        # TAB 2: ANÁLISE DETALHADA
        with tab2:
            st.markdown('<div class="animated-content">', unsafe_allow_html=True)
            
            st.subheader("🔍 Filtros Interativos Avançados")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                min_presencas = st.slider(
                    "Mínimo de Presenças:",
                    min_value=0,
                    max_value=int(presencas_por_aluno['Presenças'].max()) if not presencas_por_aluno.empty else 10,
                    value=0
                )
            
            with col2:
                min_frequencia = st.slider(
                    "Frequência Mínima (%):",
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    step=5.0
                )
            
            with col3:
                ordenar_por = st.selectbox(
                    "Ordenar por:",
                    options=['Presenças', 'Frequência (%)', 'Nome'],
                    index=0
                )
            
            # Aplicando filtros
            dados_filtrados = presencas_por_aluno[
                (presencas_por_aluno['Presenças'] >= min_presencas) &
                (presencas_por_aluno['Frequência (%)'] >= min_frequencia)
            ]
            
            if ordenar_por == 'Nome':
                dados_filtrados = dados_filtrados.sort_values('Nome')
            else:
                dados_filtrados = dados_filtrados.sort_values(ordenar_por, ascending=False)
            
            # Alertas dinâmicos
            if len(dados_filtrados) > 0:
                st.markdown(create_alert_box(
                    f"✅ <strong>{len(dados_filtrados)} alunos</strong> encontrados com os filtros aplicados",
                    "success"
                ), unsafe_allow_html=True)
            else:
                st.markdown(create_alert_box(
                    "⚠️ Nenhum aluno encontrado com os filtros aplicados",
                    "warning"
                ), unsafe_allow_html=True)
            
            # Tabela interativa
            if not dados_filtrados.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.dataframe(
                        dados_filtrados.reset_index(drop=True),
                        use_container_width=True,
                        height=400
                    )
                
                with col2:
                    # Gráfico dinâmico baseado nos filtros
                    fig_filtered = px.bar(
                        dados_filtrados.head(10),
                        x='Nome',
                        y='Presenças',
                        title="Resultado dos Filtros",
                        color='Frequência (%)',
                        color_continuous_scale='Plasma',
                        text='Presenças'
                    )
                    fig_filtered.update_layout(
                        xaxis_tickangle=45,
                        height=400,
                        title_font_size=14
                    )
                    fig_filtered.update_traces(textposition='outside')
                    st.plotly_chart(fig_filtered, use_container_width=True, key=get_unique_chart_key("dados_filtrados"))
            
            st.markdown("</div>", unsafe_allow_html=True)

        # TAB 3: BUSCA POR ALUNOS
        with tab3:
            st.markdown('<div class="animated-content">', unsafe_allow_html=True)
            
            st.subheader("🔍 Busca Inteligente de Alunos")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                busca_nomes = st.text_input(
                    "🔎 Digite parte do nome:",
                    help="Digite qualquer parte do nome para buscar"
                )
                
                nomes_disponveis = sorted(df_filtered['Nome'].unique())
                nomes_selecionados = st.multiselect(
                    "📋 Ou selecione nomes específicos:",
                    options=nomes_disponveis
                )
            
            with col2:
                st.markdown("**🎛️ Opções de Exibição:**")
                mostrar_telefone = st.checkbox("📱 Mostrar telefone", value=True)
                mostrar_como_conheceu = st.checkbox("🤝 Como conheceu", value=False)
                mostrar_primeira_vez = st.checkbox("✨ Primeira vez", value=False)
                agrupar_por_data = st.checkbox("📅 Agrupar por data", value=False)
            
            # Aplicar busca
            if busca_nomes or nomes_selecionados:
                if busca_nomes:
                    mask_busca = df_filtered['Nome'].str.contains(busca_nomes, case=False, na=False)
                    dados_busca = df_filtered[mask_busca]
                else:
                    dados_busca = df_filtered
                
                if nomes_selecionados:
                    dados_busca = dados_busca[dados_busca['Nome'].isin(nomes_selecionados)]
                
                if not dados_busca.empty:
                    st.markdown(create_alert_box(
                        f"🎯 Encontrados <strong>{len(dados_busca)} registros</strong> para <strong>{dados_busca['Nome'].nunique()} alunos</strong>",
                        "success"
                    ), unsafe_allow_html=True)
                    
                    # Análise específica
                    freq_selecionados = dados_busca.groupby('Nome').agg({
                        'Data': 'count',
                        'DDD+TELEFONE (SEM ESPAÇO)': 'first'
                    }).reset_index()
                    freq_selecionados.columns = ['Nome', 'Quantidade_Presenças', 'Telefone']
                    freq_selecionados['Frequência_Período (%)'] = (
                        freq_selecionados['Quantidade_Presenças'] / total_dias * 100
                    ).round(1) if total_dias > 0 else 0
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📊 Resumo dos Alunos Selecionados")
                        if mostrar_telefone:
                            st.dataframe(freq_selecionados, use_container_width=True)
                        else:
                            st.dataframe(freq_selecionados[['Nome', 'Quantidade_Presenças', 'Frequência_Período (%)']], use_container_width=True)
                    
                    with col2:
                        if len(freq_selecionados) > 0:
                            fig_busca = px.bar(
                                freq_selecionados,
                                x='Nome',
                                y='Quantidade_Presenças',
                                title="📈 Presenças dos Alunos Selecionados",
                                color='Frequência_Período (%)',
                                color_continuous_scale='Turbo',
                                text='Quantidade_Presenças'
                            )
                            fig_busca.update_layout(xaxis_tickangle=45)
                            fig_busca.update_traces(textposition='outside')
                            st.plotly_chart(fig_busca, use_container_width=True, key=get_unique_chart_key("busca_alunos"))
                
                else:
                    st.markdown(create_alert_box(
                        "❌ Nenhum aluno encontrado com os critérios de busca",
                        "warning"
                    ), unsafe_allow_html=True)
            
            else:
                st.markdown(create_alert_box(
                    "💡 Digite um nome ou selecione alunos para ver análise detalhada",
                    "info"
                ), unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

        # TAB 4: RELATÓRIOS
        with tab4:
            st.markdown('<div class="animated-content">', unsafe_allow_html=True)
            
            st.subheader("📄 Gerador de Relatórios Interativo")
            
            with st.expander("🎨 Configurações do Relatório", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📊 Conteúdo do Relatório**")
                    incluir_resumo_geral = st.checkbox("📈 Resumo Geral", value=True)
                    incluir_top_alunos = st.checkbox("🏆 Top Alunos Mais Assíduos", value=True)
                    incluir_baixa_freq = st.checkbox("⚠️ Alunos com Baixa Frequência", value=True)
                    incluir_atrasos = st.checkbox("⏰ Análise de Atrasos", value=True)
                    incluir_graficos = st.checkbox("📊 Gráficos", value=True)
                    incluir_tabela_completa = st.checkbox("📋 Tabela Completa", value=False)
                
                with col2:
                    st.markdown("**⚙️ Configurações**")
                    titulo_relatorio = st.text_input("📝 Título do Relatório:", value="Relatório de Frequência de Alunos")
                    
                    # Seleção de data para o relatório
                    col_data1, col_data2 = st.columns(2)
                    with col_data1:
                        data_inicio_relatorio = st.date_input(
                            "📅 Data Início:",
                            value=df_filtered['Data'].min() if not df_filtered.empty else datetime.now().date(),
                            help="Data de início do período do relatório"
                        )
                    with col_data2:
                        data_fim_relatorio = st.date_input(
                            "📅 Data Fim:",
                            value=df_filtered['Data'].max() if not df_filtered.empty else datetime.now().date(),
                            help="Data de fim do período do relatório"
                        )
                    
                    responsavel = st.text_input("👤 Responsável:", value="", help="Nome do responsável pelo relatório")
                    top_n = st.number_input("🔢 Quantidade no Top:", min_value=5, max_value=50, value=10)
                    
                    periodo_texto = f"{data_inicio_relatorio.strftime('%d/%m/%Y')} a {data_fim_relatorio.strftime('%d/%m/%Y')}"
            
            if st.button("🚀 Gerar Relatório HTML", type="primary"):
                with st.spinner("📊 Gerando relatório..."):
                    st.success("✅ Relatório gerado com sucesso!")
                    st.balloons()
                    
                    # Criar HTML simples do relatório
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>{titulo_relatorio}</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; }}
                            .header {{ text-align: center; margin-bottom: 30px; }}
                            .title {{ color: #1f77b4; font-size: 24px; font-weight: bold; }}
                            .subtitle {{ color: #666; margin: 10px 0; }}
                            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                            th {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <div class="header">
                            <div class="title">{titulo_relatorio}</div>
                            <div class="subtitle">Período: {periodo_texto}</div>
                            <div class="subtitle">Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</div>
                            {f'<div class="subtitle">Responsável: {responsavel}</div>' if responsavel else ''}
                        </div>
                        
                        <h2>Resumo Geral</h2>
                        <p>Total de Presenças: {total_presencas}</p>
                        <p>Total de Alunos: {total_alunos}</p>
                        <p>Dias de Aula: {total_dias}</p>
                        <p>Média Presenças/Dia: {media_presencas:.1f}</p>
                        
                        <h2>Top {top_n} Alunos Mais Assíduos</h2>
                        <table>
                            <tr>
                                <th>Posição</th>
                                <th>Nome</th>
                                <th>Presenças</th>
                                <th>Frequência (%)</th>
                            </tr>
                    """
                    
                    for i, (_, row) in enumerate(presencas_por_aluno.head(top_n).iterrows(), 1):
                        html_content += f"""
                            <tr>
                                <td>{i}º</td>
                                <td>{row['Nome']}</td>
                                <td>{row['Presenças']}</td>
                                <td>{row['Frequência (%)']:.1f}%</td>
                            </tr>
                        """
                    
                    html_content += """
                        </table>
                    </body>
                    </html>
                    """
                    
                    # Download do relatório
                    nome_arquivo = f"relatorio_frequencia_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
                    st.download_button(
                        label="📄 Download Relatório HTML",
                        data=html_content,
                        file_name=nome_arquivo,
                        mime="text/html"
                    )
                    
                    st.info("""
                    💡 **Como converter para PDF:**
                    1. Baixe o arquivo HTML
                    2. Abra no navegador
                    3. Pressione Ctrl+P (Cmd+P no Mac)
                    4. Selecione "Salvar como PDF"
                    """)
            
            st.markdown("</div>", unsafe_allow_html=True)

        # TAB 5: QUALIDADE DOS DADOS
        with tab5:
            st.markdown('<div class="animated-content">', unsafe_allow_html=True)
            
            st.subheader("🧹 Análise de Qualidade dos Dados")
            
            # Estatísticas de limpeza
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Estatísticas de Limpeza**")
                
                if 'Nome_Original' in df_working.columns:
                    nomes_alterados = df_working[df_working['Nome'] != df_working['Nome_Original']]
                    st.metric("✏️ Nomes Padronizados", len(nomes_alterados))
                    
                    if not nomes_alterados.empty:
                        st.markdown("**📝 Exemplos de Padronização:**")
                        exemplos = nomes_alterados[['Nome_Original', 'Nome']].drop_duplicates().head(5)
                        for _, row in exemplos.iterrows():
                            st.write(f"• `{row['Nome_Original']}` → `{row['Nome']}`")
                else:
                    st.metric("✏️ Nomes Padronizados", "N/A")
                
                st.metric("👥 Nomes Únicos", df_working['Nome'].nunique())
                st.metric("🔍 Nomes com 1 Presença", sum(df_working['Nome'].value_counts() == 1))
                st.metric("❌ Registros Vazios", df_working['Nome'].isna().sum())
            
            with col2:
                st.markdown("**⚠️ Possíveis Problemas Detectados**")
                
                from difflib import SequenceMatcher
                
                def similaridade(a, b):
                    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
                
                nomes_unicos = [nome for nome in df_working['Nome'].unique() if pd.notna(nome)]
                problemas_encontrados = []
                
                for i, nome1 in enumerate(nomes_unicos):
                    for nome2 in nomes_unicos[i+1:]:
                        if 0.8 <= similaridade(nome1, nome2) < 1.0:
                            problemas_encontrados.append((nome1, nome2, similaridade(nome1, nome2)))
                
                if problemas_encontrados:
                    st.markdown(create_alert_box(
                        f"⚠️ {len(problemas_encontrados)} pares de nomes similares detectados",
                        "warning"
                    ), unsafe_allow_html=True)
                    
                    for nome1, nome2, sim in sorted(problemas_encontrados, key=lambda x: x[2], reverse=True)[:5]:
                        st.write(f"• `{nome1}` ≈ `{nome2}` ({sim:.1%})")
                else:
                    st.markdown(create_alert_box(
                        "✅ Nenhum nome similar detectado!",
                        "success"
                    ), unsafe_allow_html=True)
            
            # FERRAMENTA DE CORREÇÃO MANUAL
            st.subheader("✏️ Corretor Manual de Nomes")
            
            with st.expander("🔧 Ferramenta de Correção", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    nome_errado = st.selectbox(
                        "🎯 Nome para corrigir:",
                        options=[''] + sorted(df_working['Nome'].unique().tolist()),
                        help="Selecione o nome que precisa ser corrigido"
                    )
                
                with col2:
                    nome_correto = st.text_input(
                        "✅ Nome correto:",
                        help="Digite o nome correto"
                    )
                
                with col3:
                    st.write("")
                    aplicar_correcao = st.button(
                        "🚀 Aplicar",
                        type="primary",
                        help="Clique para aplicar a correção"
                    )
                
                # Aplicar correção
                if aplicar_correcao and nome_errado and nome_correto and nome_errado != nome_correto:
                    mask = df_working['Nome'] == nome_errado
                    registros_alterados = mask.sum()
                    
                    if registros_alterados > 0:
                        df_working.loc[mask, 'Nome'] = nome_correto
                        st.session_state.df_corrigido = df_working
                        
                        if 'log_correcoes' not in st.session_state:
                            st.session_state.log_correcoes = []
                        
                        st.session_state.log_correcoes.append({
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'tipo': 'Correção Manual',
                            'de': nome_errado,
                            'para': nome_correto,
                            'registros': registros_alterados
                        })
                        
                        st.success(f"✅ Correção aplicada: `{nome_errado}` → `{nome_correto}` ({registros_alterados} registros)")
                        st.rerun()
                    else:
                        st.warning("⚠️ Nome não encontrado nos dados.")
                
                # Log de correções
                if 'log_correcoes' in st.session_state and st.session_state.log_correcoes:
                    st.subheader("📋 Correções Aplicadas")
                    
                    df_log = pd.DataFrame(st.session_state.log_correcoes)
                    st.dataframe(df_log, use_container_width=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🔄 Resetar Correções"):
                            st.session_state.df_corrigido = df.copy()
                            st.session_state.log_correcoes = []
                            st.success("✅ Correções resetadas!")
                            st.rerun()
                    
                    with col2:
                        csv_corrigido = df_working.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Dados Corrigidos",
                            data=csv_corrigido,
                            file_name=f"dados_corrigidos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv"
                        )
                else:
                    st.info("ℹ️ Nenhuma correção aplicada ainda.")
            
            # TOP NOMES PARA REVISÃO
            st.subheader("📋 Top 20 Nomes Mais Frequentes")
            
            top_nomes = df_working['Nome'].value_counts().head(20).reset_index()
            top_nomes.columns = ['Nome', 'Frequência']
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.dataframe(top_nomes, use_container_width=True, height=400)
            
            with col2:
                fig_top_nomes = px.bar(
                    top_nomes.head(10),
                    x='Frequência',
                    y='Nome',
                    orientation='h',
                    title="Top 10 Nomes",
                    color='Frequência',
                    color_continuous_scale='Viridis'
                )
                fig_top_nomes.update_layout(height=400)
                st.plotly_chart(fig_top_nomes, use_container_width=True, key=get_unique_chart_key("top_nomes_qualidade"))
            
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
        st.write("**💡 Possíveis soluções:**")
        st.write("• Verifique se o arquivo CSV está no formato correto")
        st.write("• Certifique-se de que as colunas obrigatórias existem")
        st.write("• Tente salvar o arquivo como CSV UTF-8")

else:
    # Landing page
    st.markdown("""
    <div class="landing-container">
        <h2>🚀 Bem-vindo ao Dashboard Interativo!</h2>
        <p class="landing-title">
            Faça upload do seu arquivo CSV na barra lateral para começar a análise
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ✨ Funcionalidades do Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(create_feature_card(
            "📊 Análise Completa",
            "Visualize frequência, atrasos, rankings e tendências",
            "blue"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_feature_card(
            "🔍 Busca Inteligente",
            "Filtre e busque alunos específicos",
            "pink"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_feature_card(
            "📄 Relatórios PDF",
            "Gere relatórios profissionais",
            "cyan"
        ), unsafe_allow_html=True)
    
    st.markdown("### 📋 Formato Esperado do Arquivo")
    
    exemplo_df = pd.DataFrame({
        'Data/hora': ['2024-01-15 19:00:00', '2024-01-15 19:05:00', '2024-01-22 18:55:00'],
        'Nome': ['João Silva', 'Maria Santos', 'João Silva'],
        'COMO CONHECEU O GRUPO?': ['Indicação', 'Redes Sociais', 'Indicação'],
        'PRIMEIRA VEZ NO GRUPO?': ['Sim', 'Não', 'Não'],
        'DDD+TELEFONE (SEM ESPAÇO)': ['11987654321', '11876543210', '11987654321']
    })
    
    st.dataframe(exemplo_df, use_container_width=True)