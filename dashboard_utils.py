"""
Utilitários para o Dashboard de Frequência de Alunos
"""

import streamlit as st
import os

def load_css(file_path="styles.css"):
    """
    Carrega arquivo CSS externo para o Streamlit
    
    Args:
        file_path (str): Caminho para o arquivo CSS
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        else:
            # CSS inline como fallback se arquivo não existir
            default_css = """
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 15px;
                color: white;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                margin-bottom: 1rem;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
            }
            
            .metric-value {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            
            .metric-label {
                font-size: 1rem;
                opacity: 0.9;
            }
            
            .success-box {
                background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white;
                margin: 1rem 0;
            }
            
            .warning-box {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white;
                margin: 1rem 0;
            }
            
            .info-box {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 1rem;
                border-radius: 10px;
                color: white;
                margin: 1rem 0;
            }
            
            .animated-content {
                animation: fadeIn 0.6s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            """
            
            st.markdown(f"<style>{default_css}</style>", unsafe_allow_html=True)
            st.warning("⚠️ Arquivo CSS não encontrado. Usando estilos padrão.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar CSS: {str(e)}")

def get_unique_chart_key(base_name):
    """
    Gera chaves únicas para gráficos Plotly
    
    Args:
        base_name (str): Nome base para a chave
        
    Returns:
        str: Chave única para o gráfico
    """
    if 'chart_counter' not in st.session_state:
        st.session_state.chart_counter = 0
    st.session_state.chart_counter += 1
    return f"{base_name}_{st.session_state.chart_counter}"

def limpar_nome(nome):
    """
    Limpa e padroniza nomes de alunos
    
    Args:
        nome (str): Nome a ser limpo
        
    Returns:
        str: Nome limpo e padronizado
    """
    import pandas as pd
    
    if pd.isna(nome):
        return nome
    nome = str(nome).strip()
    nome = ' '.join(nome.split())
    nome = nome.title()
    nome = nome.replace(' Da ', ' da ').replace(' De ', ' de ').replace(' Do ', ' do ')
    nome = nome.replace(' Das ', ' das ').replace(' Dos ', ' dos ')
    return nome

def create_metric_card(value, label):
    """
    Cria um card de métrica personalizado
    
    Args:
        value (str/int): Valor da métrica
        label (str): Rótulo da métrica
        
    Returns:
        str: HTML do card de métrica
    """
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def create_alert_box(message, box_type="info"):
    """
    Cria uma caixa de alerta personalizada
    
    Args:
        message (str): Mensagem do alerta
        box_type (str): Tipo do alerta (success, warning, info)
        
    Returns:
        str: HTML da caixa de alerta
    """
    return f"""
    <div class="{box_type}-box">
        {message}
    </div>
    """

def create_header(title, subtitle=""):
    """
    Cria o cabeçalho do dashboard
    
    Args:
        title (str): Título principal
        subtitle (str): Subtítulo (opcional)
        
    Returns:
        str: HTML do cabeçalho
    """
    subtitle_html = f'<h3 class="header-subtitle">{subtitle}</h3>' if subtitle else ''
    
    return f"""
    <div class="header-gradient">
        <h1 class="header-title">{title}</h1>
        {subtitle_html}
    </div>
    """

def create_feature_card(title, description, card_type="blue"):
    """
    Cria um card de funcionalidade
    
    Args:
        title (str): Título da funcionalidade
        description (str): Descrição da funcionalidade
        card_type (str): Tipo de card (blue, pink, cyan)
        
    Returns:
        str: HTML do card de funcionalidade
    """
    return f"""
    <div class="feature-card feature-card-{card_type}">
        <h3>{title}</h3>
        <p>{description}</p>
    </div>
    """

# Configurações globais do dashboard
DASHBOARD_CONFIG = {
    'page_title': "Dashboard Interativo - Frequência",
    'page_icon': "🎓",
    'layout': "wide",
    'initial_sidebar_state': "expanded"
}

# Colunas obrigatórias do CSV
REQUIRED_COLUMNS = [
    'Data/hora', 
    'Nome', 
    'COMO CONHECEU O GRUPO?', 
    'PRIMEIRA VEZ NO GRUPO?', 
    'DDD+TELEFONE (SEM ESPAÇO)'
]

# Configurações de cores para gráficos
CHART_COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#56ab2f',
    'warning': '#f093fb',
    'info': '#4facfe',
    'gradient_colors': ['#FF6B6B', '#FFE66D', '#4ECDC4', '#45B7D1']
}