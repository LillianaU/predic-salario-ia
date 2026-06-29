import streamlit as st
import pandas as pd
from typing import Any
from src.visualization import charts


def render_dashboard(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        fig = charts.histogram_salarios(df)
        if fig and len(fig.data) > 0:
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Muestra cómo se distribuyen los salarios promedio en las ofertas analizadas, identificando los rangos más comunes y la concentración del mercado.")

    with col2:
        fig = charts.boxplot_cargo_nivel(df)
        if fig and len(fig.data) > 0:
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Compara la mediana y variabilidad salarial entre técnicos, tecnólogos, ingenieros y seniors. Útil para ver la progresión salarial por nivel.")

    fig = charts.top_skills(df)
    if fig and len(fig.data) > 0:
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Identifica las habilidades técnicas más solicitadas en las ofertas de Medellín. El tamaño de la barra indica la frecuencia con que aparece cada skill.")

    st.markdown("#### 📊 Experiencia vs Salario Promedio")
    
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 3])
    
    with filter_col1:
        niveles_disponibles = sorted(df["cargo_nivel"].unique()) if "cargo_nivel" in df.columns else []
        nivel_map_labels = {"tecnico": "🔧 Técnico", "tecnologo": "💻 Tecnólogo", "ingeniero": "⚙️ Ingeniero", "senior": "🏆 Senior"}
        niveles_labels = [nivel_map_labels.get(n, n) for n in niveles_disponibles]
        nivelesSeleccionados = st.multiselect(
            "Nivel del cargo",
            options=niveles_labels,
            default=niveles_labels,
            key="scatter_nivel_filter",
        )
        niveles_inverse = {v: k for k, v in nivel_map_labels.items()}
        niveles_filtrar = [niveles_inverse.get(l, l) for l in nivelesSeleccionados]
    
    with filter_col2:
        modalidades_disponibles = sorted(df["modalidad_clean"].unique()) if "modalidad_clean" in df.columns else []
        modal_map_labels = {"presencial": "🏢 Presencial", "hibrido": "🔄 Híbrido", "remoto": "🏠 Remoto"}
        modalidades_labels = [modal_map_labels.get(m, m) for m in modalidades_disponibles]
        modalidadesSeleccionadas = st.multiselect(
            "Modalidad",
            options=modalidades_labels,
            default=modalidades_labels,
            key="scatter_modal_filter",
        )
        modalidades_inverse = {v: k for k, v in modal_map_labels.items()}
        modalidades_filtrar = [modalidades_inverse.get(m, m) for m in modalidadesSeleccionadas]
    
    with filter_col3:
        if "experiencia_requerida" in df.columns and df["experiencia_requerida"].max() > 0:
            exp_min = int(df["experiencia_requerida"].min())
            exp_max = int(df["experiencia_requerida"].max())
            rango_exp = st.slider(
                "Rango de experiencia (años)",
                min_value=exp_min,
                max_value=exp_max,
                value=(exp_min, exp_max),
                key="scatter_exp_filter",
            )
        else:
            rango_exp = (0, 20)
    
    df_filtrada = df.copy()
    if niveles_filtrar:
        df_filtrada = df_filtrada[df_filtrada["cargo_nivel"].isin(niveles_filtrar)]
    if modalidades_filtrar:
        df_filtrada = df_filtrada[df_filtrada["modalidad_clean"].isin(modalidades_filtrar)]
    if "experiencia_requerida" in df_filtrada.columns:
        df_filtrada = df_filtrada[
            (df_filtrada["experiencia_requerida"] >= rango_exp[0]) & 
            (df_filtrada["experiencia_requerida"] <= rango_exp[1])
        ]
    
    fig = charts.scatter_experiencia_salario(df_filtrada)
    if fig and len(fig.data) > 0:
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Relaciona los años de experiencia con el salario ofrecido. La línea de tendencia muestra el crecimiento salarial esperado a medida que aumenta la experiencia.")
    else:
        st.info("No hay datos para los filtros seleccionados.")
    
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    with stats_col1:
        if not df_filtrada.empty and "salario_promedio" in df_filtrada.columns:
            avg_sal = df_filtrada["salario_promedio"].mean()
            st.metric("Salario Promedio", f"${avg_sal:,.0f}")
    with stats_col2:
        if not df_filtrada.empty and "salario_promedio" in df_filtrada.columns:
            med_sal = df_filtrada["salario_promedio"].median()
            st.metric("Salario Mediana", f"${med_sal:,.0f}")
    with stats_col3:
        st.metric("Ofertas filtradas", f"{len(df_filtrada)}")

    col3, col4 = st.columns(2)
    with col3:
        fig = charts.heatmap_cargo_modalidad(df)
        if fig and len(fig.data) > 0:
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Salario promedio cruzando nivel del cargo con modalidad de trabajo (presencial, remoto, híbrido). Revela qué combinaciones pagan mejor.")

    with col4:
        fig = charts.timeline_ofertas(df)
        if fig and len(fig.data) > 0 and fig.data[0].x is not None and len(fig.data[0].x) > 1:
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Cantidad de ofertas publicadas a lo largo del tiempo. Ayuda a identificar estacionalidad y tendencias en la contratación del sector TI en Medellín.")
