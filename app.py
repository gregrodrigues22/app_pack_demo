# --- Set up
import streamlit as st  
import plotly.graph_objects as go
import numpy as np
from google.cloud import bigquery
import pandas as pd
import json
from scipy.stats import linregress
from plotly.subplots import make_subplots
from plotly.colors import sequential
import os

#gcloud auth application-default login
#~/.local/bin/streamlit run app.py --server.port=8080 --server.enableCORS=false --server.enableXsrfProtection=false --server.address=0.0.0.0

# --- Título e Layout do Streamlit
st.set_page_config(layout="wide", page_title="Análise de AIHs por Grão")

# --- Configurações do BigQuery 
PROJECT_ID = "escolap2p" 
TABLE_ID = "cliente_packbrasil.sih_aplications" 

with open("/tmp/keyfile.json", "w") as f:
    json.dump(st.secrets["bigquery"].to_dict(), f)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/keyfile.json"

client = bigquery.Client()

# --- Aquisição de dados do BigQuery
@st.cache_data
def consultar_dados():
    client = bigquery.Client()
    query = """
        SELECT
            *
        FROM
            `escolap2p.cliente_packbrasil.sih_icsap_pack_demo`
    """
    return client.query(query).to_dataframe()

# Executa a query e transforma em DataFrame
df = consultar_dados()

# --- Barra Lateral
faixas_etarias_options = sorted(df['FAIXA_ETARIA'].dropna().unique().tolist())
sexo_options = df['SEXO_DESC'].dropna().unique().tolist()
tipo_internamento_options = df['TIPO_INTERNAMENTO'].dropna().unique().tolist()
local_atendimento_options = df['LOCAL_ATENDIMENTO'].dropna().unique().tolist()
anos_options = sorted(df['ANO_INT'].dropna().unique().tolist(), reverse=True) # Ordena do mais novo para o mais antigo
meses_options = sorted(df['MES_INT'].dropna().unique().tolist())
quintil_custo_options = sorted(df['QUINTIL_CUSTO'].dropna().unique().tolist())
capitulo_cid_options = sorted(df['capitulo'].dropna().unique().tolist())
tipo_icsap_options = df['icsap'].dropna().unique().tolist() # Já renomeados para ICSAP/Não-ICSAP
tipo_vinculo_options = df['TIPO_VINC_SUS'].dropna().unique().tolist()
tipo_gestao_options = df['TIPO_GESTAO'].dropna().unique().tolist()
cnes_options = sorted(df['CNES'].dropna().unique().tolist())

st.sidebar.image("logo.png", width=400)  # ajuste o width conforme necessário
st.sidebar.title("🔎 Filtros")

# --- Fatores do Paciente ---
with st.sidebar.expander("Fatores do Paciente", expanded=False):
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

# --- Fatores da Internação ---
with st.sidebar.expander("Fatores da Internação", expanded=False):
    selected_tipo_internamento = st.multiselect(
        "Tipo de internamento",
        options=tipo_internamento_options,
        default=tipo_internamento_options
    )
    selected_local_atendimento = st.multiselect(
        "Local de atendimento",
        options=local_atendimento_options,
        default=local_atendimento_options
    )
    selected_ano_int = st.multiselect(
        "Ano da internação",
        options=anos_options,
        default=anos_options
    )
    selected_mes_int = st.multiselect(
        "Mês da internação",
        options=meses_options,
        default=meses_options
    )
    selected_quintil_custo = st.multiselect(
        "Quintil de custo",
        options=quintil_custo_options,
        default=quintil_custo_options
    )

# --- Fatores do Motivo da Internação ---
with st.sidebar.expander("Fatores do Motivo da Internação", expanded=False):
    selected_capitulo_cid = st.multiselect(
        "Capítulo CID",
        options=capitulo_cid_options,
        default=capitulo_cid_options
    )
    selected_tipo_icsap = st.multiselect(
        "Tipo ICSAP",
        options=tipo_icsap_options,
        default=tipo_icsap_options
    )

# --- Fatores do Hospital ---
with st.sidebar.expander("Fatores do Hospital", expanded=False):
    selected_cnes = st.multiselect(
        "Estabelecimento (CNES)",
        options=cnes_options,
        default=cnes_options
    )
    selected_tipo_gestao = st.multiselect(
        "Tipo de gestão",
        options=tipo_gestao_options,
        default=tipo_gestao_options
    )
    selected_tipo_vinculo = st.multiselect(
        "Tipo de vínculo SUS",
        options=tipo_vinculo_options,
        default=tipo_vinculo_options
    )

# CSS personalizado com degradê
st.markdown("""
<style>
    /* Degradê atrás do título principal */
    .title-with-gradient {
        background: linear-gradient(90deg, #011f4b 0%, #2a5298 100%);
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
tab1, tab2, tab3 = st.tabs(["➗ Por Contagem e Proporção de Internação", "💰 Por Custo de Internação", "🧮 Por Coeficiente de Internação"])

with tab1:

    #GRÁFICO 1
    
    # Realiza o groupby por 'IS_ICSAP' e soma 'total_aih_distintos_neste_grao'
    df_agregado = df.groupby('IS_ICSAP')['total_aih_distintos_neste_grao'].sum().reset_index()
    df_agregado.columns = ['IS_ICSAP', 'Soma_AIH_Distintos']
    df_agregado['IS_ICSAP'] = df_agregado['IS_ICSAP'].replace({'Sim': 'ICSAP','Não': 'Não-ICSAP'})
    total_internacoes = df_agregado['Soma_AIH_Distintos'].sum()
    percentuais = (df_agregado['Soma_AIH_Distintos'] / df_agregado['Soma_AIH_Distintos'].sum()) * 100

    # Dados
    val_icsap = df_agregado.loc[df_agregado['IS_ICSAP'] == 'ICSAP', 'Soma_AIH_Distintos'].values[0]
    val_nao_icsap = df_agregado.loc[df_agregado['IS_ICSAP'] == 'Não-ICSAP', 'Soma_AIH_Distintos'].values[0]

    # Organiza valores
    valores = [val_nao_icsap, val_icsap]
    categorias = ["Não-ICSAP", "ICSAP"]
    total = sum(valores)
    percentuais = [v / total * 100 for v in valores]

    # Cores
    cores_personalizadas = {
        'ICSAP': 'rgb(3, 57, 108)',
        'Não-ICSAP': 'rgb(0, 91, 150)',
    }
    cores = [cores_personalizadas[c] for c in categorias]

    # Texto da variação
    diferenca = abs(val_nao_icsap - val_icsap)
    razao = val_nao_icsap / val_icsap
    texto_var = f"{diferenca:,.0f} internações | razão = {razao:.2f}x"
    texto_var = texto_var.replace(",", "X").replace(".", ",").replace("X", ".")

    # Rótulos dentro das barras
    def format_label(valor, percentual):
        val_str = f"{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        pct_str = f"{percentual:.1f}".replace(".", ",")
        return f"N = {val_str}<br>{pct_str}%"

    labels = [format_label(v, p) for v, p in zip(valores, percentuais)]

    # Gráfico
    fig_1 = go.Figure()

    fig_1.add_trace(go.Bar(
        x=categorias,
        y=valores,
        text=labels,
        textposition="inside",
        marker_color=cores,
        width=[0.4, 0.4]
    ))

    # Linhas estilo π invertido
    y_top = max(valores) * 1.1
    fig_1.add_shape(type="line", x0=0, y0=valores[0], x1=0, y1=y_top,
                line=dict(color="gray", width=2))
    fig_1.add_shape(type="line", x0=1, y0=valores[1], x1=1, y1=y_top,
                line=dict(color="gray", width=2))
    fig_1.add_shape(type="line", x0=0, y0=y_top, x1=1, y1=y_top,
                line=dict(color="gray", width=2))

    # Anotação central em cinza
    fig_1.add_annotation(
        x=0.5,
        y=y_top + max(valores) * 0.05,
        text=texto_var,
        showarrow=False,
        font=dict(size=14, color="gray"),
        xanchor="center"
    )

    # Layout maior e sem grid
    fig_1.update_layout(
        title="Comparativo de Internações Distintas por ICSAP",
        yaxis_title="Total de AIHs distintos",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        height=600,
        width=800,
        yaxis=dict(showgrid=False),
        xaxis=dict(showgrid=False)
    )

    #GRÁFICO 2:

    # Filtra apenas ICSAP
    df_icsap = df[df['IS_ICSAP'] == 'Sim']

    # Agrupa por ano e mês e soma
    tabela = df_icsap.groupby(['ANO_INT', 'MES_INT'])['total_aih_distintos_neste_grao'].sum().reset_index()

    # Converte para milhares
    tabela['milhares'] = tabela['total_aih_distintos_neste_grao'] / 1000

    # Cria matriz para o heatmap
    heatmap_data = tabela.pivot(index='ANO_INT', columns='MES_INT', values='milhares').fillna(0)

    # Totais marginais
    totais_colunas = heatmap_data.sum(axis=0)  # por mês
    totais_linhas = heatmap_data.sum(axis=1)  # por ano

    # Textos formatados para o heatmap
    text_labels = [[f"{val:.1f}k" for val in row] for row in heatmap_data.values]

    # Cor azul para as barras marginais (tom intermediário da escala)
    cor_azul_marginal = 'rgb(0, 91, 150)'

    # Subplots: heatmap + barras marginais
    fig_2 = make_subplots(
        rows=2, cols=2,
        column_widths=[0.85, 0.15],
        row_heights=[0.15, 0.85],
        shared_xaxes=True,
        shared_yaxes=True,
        vertical_spacing=0.02,
        horizontal_spacing=0.02,
        specs=[[{"type": "bar"}, None],
            [{"type": "heatmap"}, {"type": "bar"}]]
    )

    # Heatmap central
    fig_2.add_trace(go.Heatmap(
        z=heatmap_data.values,
        x=[int(m) for m in heatmap_data.columns],
        y=[int(a) for a in heatmap_data.index],
        text=text_labels,
        colorscale="Blues",
        hovertemplate="Ano: %{y}<br>Mês: %{x}<br>Total: %{z:.1f} mil<extra></extra>"
    ), row=2, col=1)

    # Barras inferiores (totais por mês) com rótulos
    fig_2.add_trace(go.Bar(
        x=totais_colunas.index,
        y=totais_colunas.values,
        marker_color=cor_azul_marginal,
        text=[f"{v:.1f}k" for v in totais_colunas.values],
        textposition="auto",  # ou "auto"
        showlegend=False,
        textfont=dict(color='white')
    ), row=1, col=1)

    # Barras laterais (totais por ano) com rótulos
    fig_2.add_trace(go.Bar(
        y=totais_linhas.index,
        x=totais_linhas.values,
        orientation='h',
        marker_color=cor_azul_marginal,
        text=[f"{v:.1f}k" for v in totais_linhas.values],
        textposition="auto",  # ou "auto"
        showlegend=False,
        textfont=dict(color='white')
    ), row=2, col=2)

    # Layout final
    fig_2.update_layout(
        title="Internações ICSAP por Ano e Mês (em milhares) com Totais Marginais",
        height=600,
        width=900,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin=dict(t=50, l=50, r=100)  # r=80 ou mais, dependendo do tamanho do texto
    )

    fig_2.update_xaxes(showgrid=False, title_text="Mês", row=2, col=1)
    fig_2.update_yaxes(showgrid=False, title_text="Ano", row=2, col=1)

    # Remove grade das barras marginais
    fig_2.update_xaxes(showgrid=False, row=1, col=1)  # topo
    fig_2.update_yaxes(showgrid=False, row=2, col=2)  # lateral

    #GRÁFICO 3:

    # Agrupar por 'icsap' e somar os AIHs distintos
    df_contagem_cid_pareto = df_icsap.groupby('icsap').agg(
        contagem_id=('total_aih_distintos_neste_grao', 'sum')
    ).reset_index()

    # Ordenar por contagem decrescente
    df_contagem_cid_pareto = df_contagem_cid_pareto.sort_values(by='contagem_id', ascending=False)

    # Calcular porcentagem acumulada
    df_contagem_cid_pareto['cumulative_percentage'] = (
        df_contagem_cid_pareto['contagem_id'].cumsum() / df_contagem_cid_pareto['contagem_id'].sum()
    ) * 100

    # Criar rótulo com número e percentual formatado
    df_contagem_cid_pareto['label'] = df_contagem_cid_pareto.apply(
        lambda row: f"{row['contagem_id']:,} ({row['cumulative_percentage']:.1f}%)".replace(",", "."),
        axis=1
    )

    # Definir cores com base na regra de 80%
    cor_acima_media = 'rgb(3, 57, 108)'         # Azul escuro
    cor_abaixo_media = 'rgb(179, 205, 224)'     # Azul claro
    cores = [
        cor_acima_media if pct < 80 else cor_abaixo_media
        for pct in df_contagem_cid_pareto["cumulative_percentage"]
    ]

    # Criar gráfico de Pareto
    fig_3 = go.Figure()

    # Barras de frequência com rótulo combinado
    fig_3.add_trace(go.Bar(
        x=df_contagem_cid_pareto["icsap"],
        y=df_contagem_cid_pareto["contagem_id"],
        name="Frequência",
        marker=dict(color=cores),
        text=df_contagem_cid_pareto["label"],
        textposition="outside",
        textfont=dict(size=14),
        yaxis="y1"
    ))

    # Linha da porcentagem acumulada
    fig_3.add_trace(go.Scatter(
        x=df_contagem_cid_pareto["icsap"],
        y=df_contagem_cid_pareto["cumulative_percentage"],
        name="Porcentagem Acumulada",
        yaxis="y2",
        mode="lines+markers",
        marker=dict(color="red"),
        line=dict(width=3)
    ))

    # Layout do gráfico
    fig_3.update_layout(
        title=dict(
            text="Distribuição de Internações por Tipo ICSAP com Porcentagem Acumulada",
            font=dict(size=18)
        ),
        xaxis=dict(
            title=dict(text="Grupo de ICSAP", font=dict(size=18)),
            tickfont=dict(size=14),
            showgrid=False
        ),
        yaxis=dict(
            title=dict(text="Frequência", font=dict(size=18)),
            tickfont=dict(size=14),
            showgrid=False
        ),
        yaxis2=dict(
            title=dict(text="Porcentagem Acumulada (%)", font=dict(size=18)),
            tickfont=dict(size=14),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        legend=dict(
            x=0.8, y=1.15,
            font=dict(size=14)
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(size=14),
        width=1300,
        height=600
    )

    # Cria 2 colunas: a primeira com largura '1' e a segunda com largura '2'
    col_grafico1, col_grafico2 = st.columns([1, 2])

    with col_grafico1:
        st.plotly_chart(fig_1, use_container_width=True, height=600) # use_container_width é importante aqui para preencher a largura da coluna

    with col_grafico2:
        st.plotly_chart(fig_2, use_container_width=True, height=600) # use_container_width é importante aqui para preencher a largura da coluna

    st.plotly_chart(fig_3, use_container_width=True, height=400)

with tab2:
    st.subheader("🏗️ Em obras")
    # Aqui você pode adicionar a visualização gráfica do canvas
    st.write("Em vista do CBMFC e da prova ingresso no doutorado, tive apenas um dia para trabalhar no projeto 😅")

with tab3:
    st.subheader("🏗️ Em obras")
    # Lista de templates
    st.write("Em vista do CBMFC e da prova ingresso no doutorado, tive apenas um dia para trabalhar no projeto 😅")





