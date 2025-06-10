# --- Set up
import streamlit as st  
import plotly.graph_objects as go
import numpy as np
from google.cloud import bigquery
import pandas as pd
import json
from scipy.stats import linregress

#gcloud auth application-default login
#~/.local/bin/streamlit run app.py --server.port=8080 --server.enableCORS=false --server.enableXsrfProtection=false --server.address=0.0.0.0

# --- Título e Layout do Streamlit
st.set_page_config(layout="wide", page_title="Análise de AIHs por Grão")

# --- Configurações do BigQuery 
PROJECT_ID = "escolap2p" 
TABLE_ID = "cliente_packbrasil.sih_aplications" 

# --- Aquisição de dados do BigQuery
@st.cache_data
def consultar_dados():
    client = bigquery.Client()
    query = """
        SELECT
            *
        FROM
            `escolap2p.cliente_packbrasil.sih_icsap_pack_demo`
        #LIMIT 10000
    """
    return client.query(query).to_dataframe()

# Executa a query e transforma em DataFrame
df = consultar_dados()

# --- Barra Lateral
faixas_etarias_options = sorted(df['FAIXA_ETARIA'].unique().tolist())
sexo_options = df['SEXO_DESC'].unique().tolist()
tipo_internamento_options = df['TIPO_INTERNAMENTO'].unique().tolist()
local_atendimento_options = df['LOCAL_ATENDIMENTO'].unique().tolist()
anos_options = sorted(df['ANO_INT'].unique().tolist(), reverse=True) # Ordena do mais novo para o mais antigo
meses_options = sorted(df['MES_INT'].unique().tolist())
quintil_custo_options = sorted(df['QUINTIL_CUSTO'].unique().tolist())
capitulo_cid_options = sorted(df['capitulo'].unique().tolist())
tipo_icsap_options = df['icsap'].unique().tolist() # Já renomeados para ICSAP/Não-ICSAP
tipo_vinculo_options = df['TIPO_VINC_SUS'].unique().tolist()
tipo_gestao_options = df['TIPO_GESTAO'].unique().tolist()
cnes_options = sorted(df['CNES'].unique().tolist())

st.sidebar.image("logo.png", width=400)  # ajuste o width conforme necessário
st.sidebar.title("🔎 Filtros")

# --- Fatores do Paciente ---
with st.sidebar.expander("Fatores do Paciente", expanded=True):
    selected_faixa_etaria = st.multiselect(
        "Faixa etária",
        options=faixas_etarias_options,
        default=faixas_etarias_options # Seleciona todos por padrão
    )
    selected_sexo = st.multiselect(
        "Sexo",
        options=sexo_options,
        default=sexo_options
    )

# CSS personalizado com degradê
st.markdown("""
<style>
    /* Degradê atrás do título principal */
    .title-with-gradient {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Estilos adicionais para manter a consistência */
    .block-container {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    .st-expander .st-emotion-cache-1q7spjk {
        border: 1px solid #3498db;
        border-radius: 5px;
    }
        /* Espaço acima do título */
    .title-with-gradient::before {
        content: "";
        display: block;
        height: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Título principal com degradê
st.markdown(
    """
    <div class="title-with-gradient">
        <h1 style="margin:10;padding:0;"> 📊 Análise de ICSAPs (SIH)</h1>
        <p style="margin:10;padding:0;font-size:16px;">Explore a ocorrência de ICSAPs escolhendo a métrica e aplicando filtros nas dimensões.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Abas para diferentes seções
tab1, tab2, tab3 = st.tabs(["➗ Por Proporção de Internação", "💰 Por Custo de Internação", "🧮 Por Coeficiente de Internação"])

with tab1:

    #GRÁFICO 1
    
    # Realiza o groupby por 'IS_ICSAP' e soma 'total_aih_distintos_neste_grao'
    df_agregado = df.groupby('IS_ICSAP')['total_aih_distintos_neste_grao'].sum().reset_index()
    df_agregado.columns = ['IS_ICSAP', 'Soma_AIH_Distintos']
    df_agregado['IS_ICSAP'] = df_agregado['IS_ICSAP'].replace({'Sim': 'ICSAP','Não': 'Não-ICSAP'})
    total_internacoes = df_agregado['Soma_AIH_Distintos'].sum()
    percentuais = (df_agregado['Soma_AIH_Distintos'] / df_agregado['Soma_AIH_Distintos'].sum()) * 100
    #st.dataframe(df_agregado, use_container_width=True) # Exibe o DataFrame como uma tabela interativa


    # Definir cores personalizadas usando RGB (modifique conforme desejar)
    cores_personalizadas = {
        'ICSAP': 'rgb(30, 60, 114)', 
        'Não-ICSAP': 'rgb(80, 115, 150)', 
    }

    # Criar gráfico de pizza com valores absolutos e percentuais
    fig_1 = go.Figure(data=[
        go.Pie(
            labels=df_agregado['IS_ICSAP'],
            values=df_agregado['Soma_AIH_Distintos'],
            text=[f"{v} ({p:.1f}%)" for v, p in zip(df_agregado['Soma_AIH_Distintos'], percentuais)],  # Rótulo com absoluto e percentual
            textinfo='text',  # Mostrar apenas os rótulos personalizados
            textfont=dict(size=18),  # Tamanho dos rótulos
            marker=dict(colors=[cores_personalizadas.get(label, 'rgb(169, 169, 169)') for label in df_agregado['IS_ICSAP']]),  # Aplicar cores personalizadas, default cinza
            hole=0.5  # Pizza sem buraco (gráfico padrão de setores)
        )
    ])

    # Atualizar layout do gráfico
    fig_1.update_layout(
        title='Qual foi o percentual de ICSAP em todo o período?',
        font=dict(size=30),  # Tamanho do título
        #x=0.5,  # Centraliza o título
        paper_bgcolor='white',
        plot_bgcolor='white',
        width=1300,
        height=700
    )

    fig_1.update_layout(
        showlegend=True,
        legend=dict(
            font=dict(size=16),  # Tamanho da legenda
            orientation='h',     # 'h' para horizontal
            x=0.5,              # Posição horizontal da legenda
            xanchor='center',    # Centraliza a posição horizontal
            y=1,                  # Posição vertical da legenda
            yanchor='bottom'   # Ancoragem da legenda (parte de baixo da legenda fica em y=1.00)
        )
    )

    # Adicionar o valor total no centro da rosca
    fig_1.add_annotation(
        text=f"Total:<br>{total_internacoes:,}",
        x=0.5, y=0.5,
        font=dict(size=18, color='black'),
        showarrow=False,
        xanchor='center',
        yanchor='middle'
    )

    #GRÁFICO 2:

    # Realiza o groupby por 'Ano' e soma 'total_aih_distintos_neste_grao'
    df['atendimento_data'] = pd.to_datetime(df['ANO_INT'].astype(str) + '-' + df['MES_INT'].astype(str) + '-01')

    if not df.empty: # Verifica se o DataFrame não está vazio
        max_date = df['atendimento_data'].max() # Encontra a data mais recente
        # Calcula a data de início do período de 12 meses
        # Subtrai 11 meses para incluir o mês max_date, totalizando 12 meses.
        # Ex: se max_date é 2024-02-01, start_date será 2023-03-01.
        start_date_12_months = max_date - pd.DateOffset(months=11)

        # Filtra o DataFrame
        df_filtrado_12_meses = df[df['atendimento_data'] >= start_date_12_months].copy()
    else:
        df_filtrado_12_meses = pd.DataFrame() 

    df_atendimento_agrupado = df_filtrado_12_meses.groupby(['atendimento_data','IS_ICSAP'])['total_aih_distintos_neste_grao'].sum().reset_index()
    df_atendimento_agrupado.rename(columns={'atendimento_id': 'numero_atendimento'}, inplace=True)

    # Pivotar o DataFrame para ter ICSAP e Não-ICSAP como colunas
    df_proporcao = df_atendimento_agrupado.pivot_table(
        index='atendimento_data',
        columns='IS_ICSAP',
        values='total_aih_distintos_neste_grao'
    ).fillna(0).reset_index() # .fillna(0) para garantir que meses sem uma categoria não causem NaN

    # Calcular o Total por mês
    df_proporcao['Total_Mensal'] = df_proporcao['Sim'] + df_proporcao['Não']

    # Calcular a Proporção de ICSAP (garantir que não dividimos por zero)
    df_proporcao['Proporcao_ICSAP'] = df_proporcao.apply(
        lambda row: row['Sim'] / row['Total_Mensal'] if row['Total_Mensal'] > 0 else 0,
        axis=1
    )

    df_proporcao['atendimento_mes_texto'] = df_proporcao['atendimento_data'].dt.to_period('M').astype(str)

    # Calcular a média mensal
    media_mensal = df_proporcao['Proporcao_ICSAP'].mean()

    # Definir as novas cores ---
    cor_acima_media = 'rgb(0, 82, 164)'    # Azul mais escuro/intenso
    cor_abaixo_media = 'rgb(30, 144, 255)' # Azul mais claro/suave
    cor_menor_valor = 'rgb(228, 46, 68)'   # Vermelho
    cor_maior_valor = 'rgb(65, 134, 84)'   # Verde

    # Cálculos principais
    maior_valor = df_proporcao['Proporcao_ICSAP'].max()
    menor_valor = df_proporcao['Proporcao_ICSAP'].min()
    media_mensal = df_proporcao['Proporcao_ICSAP'].mean()
    df_proporcao['variacao_percentual'] = df_proporcao['Proporcao_ICSAP'].pct_change() * 100
    df_proporcao['indice'] = range(len(df_proporcao))

    # Tendência
    slope, intercept, *_ = linregress(
        df_proporcao['indice'],
        df_proporcao['Proporcao_ICSAP']
    )
    df_proporcao['tendencia'] = intercept + slope * df_proporcao['indice']

    # Função de cor
    def determinar_cor(valor):
        if valor == maior_valor:
            return cor_maior_valor
        elif valor == menor_valor:
            return cor_menor_valor
        elif valor > media_mensal:
            return cor_acima_media
        else:
            return cor_abaixo_media

    # Criar figura
    fig_2 = go.Figure()

    # Barras de atendimentos
    fig_2.add_trace(go.Bar(
        x=df_proporcao['atendimento_data'],
        y=df_proporcao['Proporcao_ICSAP'],
        name='Atendimentos',
        marker_color=[determinar_cor(v) for v in df_proporcao['Proporcao_ICSAP']],
        text=df_proporcao['Proporcao_ICSAP'],
        textposition='outside',
        textfont_size=18,
        showlegend=False
    ))

    # Linha de tendência
    fig_2.add_trace(go.Scatter(
        x=df_proporcao['atendimento_data'],
        y=df_proporcao['tendencia'],
        mode='lines',
        name='Tendência',
        line=dict(color='blue', dash='dash')
    ))

    # Texto PoP
    for i, row in df_proporcao.iterrows():
        if not np.isnan(row['variacao_percentual']):
            seta = '▲' if row['variacao_percentual'] > 0 else '▼'
            cor = 'green' if row['variacao_percentual'] > 0 else 'red'
            texto = f"{seta} {abs(row['variacao_percentual']):.2f}%"
            fig_2.add_annotation(
                x=row['atendimento_data'],
                y=row['Proporcao_ICSAP'],
                text=texto,
                showarrow=False,
                font=dict(size=12, color=cor),
                yshift=30
            )

    # Linha da média
    fig_2.add_hline(
        y=media_mensal,
        line_dash='dash',
        line_color='lightgray',
        annotation_text=f"<b>Média: {media_mensal:.2f}</b>",
        annotation_font_color='black'
    )

    # Layout final
    fig_2.update_layout(
        title='<b>Atendimentos por Competência</b>',
        xaxis_title='Competência',
        yaxis_title='Número de Atendimentos',
        paper_bgcolor='white',
        plot_bgcolor='white',
        width=1300,
        height=800,
        barmode='stack'
    )

    # Eixo X: usa a data real mas mostra o texto
    fig_2.update_xaxes(
        tickmode='array',
        tickvals=df_proporcao['atendimento_data'],
        ticktext=df_proporcao['atendimento_mes_texto'],
        title_font_size=20,
        showticklabels=True
    )

    fig_2.update_yaxes(showticklabels=False, title_font_size=20)

    # Cria 2 colunas: a primeira com largura '1' e a segunda com largura '2'
    col_grafico1, col_grafico2 = st.columns([1, 2])

    with col_grafico1:
        st.plotly_chart(fig_1) # use_container_width é importante aqui para preencher a largura da coluna

    with col_grafico2:
        st.plotly_chart(fig_2) # use_container_width é importante aqui para preencher a largura da coluna

with tab2:
    st.subheader("Visualização do Canvas")
    # Aqui você pode adicionar a visualização gráfica do canvas
    st.write("Visualização do canvas será exibida aqui")

with tab3:
    st.subheader("Templates Disponíveis")
    # Lista de templates
    st.write("Lista de templates disponíveis")





