import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Any

_PRIMARY = "#4A90E2"
_SECONDARY = "#2557CC"
_ACCENT = "#1B3F8B"
_COLORS = [_PRIMARY, _SECONDARY, "#0A1F50", "#6AABF0", "#f59e0b", "#ec4899"]
_BG = "rgba(0,0,0,0)"
_FONT = "Inter, 'Segoe UI', sans-serif"


def _base_layout(title: str, x_title: str = "", y_title: str = "") -> dict:
    return {
        "title": {
            "text": title,
            "font": {"family": _FONT, "size": 18, "color": "#FFFFFF", "weight": 700},
            "x": 0.02,
            "xanchor": "left",
            "y": 0.97,
        },
        "paper_bgcolor": _BG,
        "plot_bgcolor": _BG,
        "font": {"family": _FONT, "color": "#B0C4DE"},
        "xaxis": {
            "title": {"text": x_title, "font": {"size": 13, "color": "#B0C4DE"}},
            "gridcolor": "rgba(74,144,226,0.1)",
            "zerolinecolor": "rgba(74,144,226,0.15)",
            "tickfont": {"size": 12, "color": "#B0C4DE"},
        },
        "yaxis": {
            "title": {"text": y_title, "font": {"size": 13, "color": "#B0C4DE"}},
            "gridcolor": "rgba(74,144,226,0.1)",
            "zerolinecolor": "rgba(74,144,226,0.15)",
            "tickfont": {"size": 12, "color": "#B0C4DE"},
        },
        "hoverlabel": {
            "bgcolor": "#1B3F8B",
            "font": {"color": "#FFFFFF", "family": _FONT, "size": 13},
            "bordercolor": "rgba(74,144,226,0.4)",
        },
        "margin": {"t": 50, "b": 30, "l": 10, "r": 10},
        "legend": {
            "font": {"color": "#B0C4DE", "size": 12},
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "rgba(0,0,0,0)",
        },
        "dragmode": False,
    }


def _empty_fig(msg: str = "No hay datos disponibles") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=f"<b>{msg}</b>",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False,
        font={"size": 16, "color": "#64748b", "family": _FONT},
    )
    fig.update_layout(**_base_layout(""))
    fig.update_layout(xaxis_visible=False, yaxis_visible=False)
    return fig


def histogram_salarios(df: pd.DataFrame, col: str = "salario_promedio") -> Any:
    if df.empty or col not in df.columns or df[col].dropna().empty:
        return _empty_fig()
    fig = px.histogram(
        df, x=col, nbins=25, marginal="box",
        title="Distribución de Salarios Promedio",
        labels={col: "Salario Promedio (COP)", "count": "Frecuencia"},
        color_discrete_sequence=[_PRIMARY],
        opacity=0.7,
        histnorm=None,
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate="<b>Salario:</b> $%{x:,.0f}<br><b>Ofertas:</b> %{y}<extra></extra>",
    )
    fig.update_layout(
        **_base_layout(
            "Distribución de Salarios Promedio",
            "Salario Promedio (COP)", "Número de Ofertas"
        ),
        xaxis_tickformat="$,.0f",
        bargap=0.04,
        boxgap=0.15,
    )
    return fig


def boxplot_cargo_nivel(df: pd.DataFrame) -> Any:
    if df.empty or "cargo_nivel" not in df.columns or df["salario_promedio"].dropna().empty:
        return _empty_fig()
    level_names = {"tecnico": "Técnico", "tecnologo": "Tecnólogo", "ingeniero": "Ingeniero", "senior": "Senior"}
    dff = df.copy()
    dff["cargo_nivel_label"] = dff["cargo_nivel"].map(level_names).fillna(dff["cargo_nivel"])
    fig = px.box(
        dff, x="cargo_nivel_label", y="salario_promedio", color="cargo_nivel_label",
        title="Distribución Salarial por Nivel de Cargo",
        labels={"cargo_nivel_label": "Nivel del Cargo", "salario_promedio": "Salario Promedio (COP)"},
        color_discrete_sequence=_COLORS,
        category_orders={
            "cargo_nivel_label": ["Técnico", "Tecnólogo", "Ingeniero", "Senior"]
        },
        points="outliers",
        notched=True,
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>Salario: $%{y:,.0f}<extra></extra>",
        marker_size=5,
        line={"width": 1.5},
    )
    fig.update_layout(
        **_base_layout(
            "Distribución Salarial por Nivel de Cargo",
            "Nivel del Cargo", "Salario Promedio (COP)"
        ),
        yaxis_tickformat="$,.0f",
        showlegend=False,
    )
    return fig


def _extract_skills_safe(df: pd.DataFrame) -> list:
    all_skills = []
    if "skills_list" in df.columns:
        for s in df["skills_list"]:
            if isinstance(s, list):
                all_skills.extend(s)
        if all_skills:
            return all_skills
    if "skills_str" in df.columns:
        for s in df["skills_str"].dropna():
            parts = [x.strip() for x in str(s).split(",") if x.strip()]
            all_skills.extend(parts)
    if not all_skills and "skills" in df.columns:
        for s in df["skills"].dropna():
            parts = [x.strip() for x in str(s).split(",") if x.strip()]
            all_skills.extend(parts)
    return all_skills


def top_skills(df: pd.DataFrame, top_n: int = 12) -> Any:
    all_skills = _extract_skills_safe(df)
    if not all_skills:
        return _empty_fig("No se encontraron skills en los datos")
    skill_counts = pd.Series(all_skills).value_counts().head(top_n)
    max_val = skill_counts.max()
    pct = ((skill_counts / max_val) * 100).round(1)
    colors = []
    for v in pct.values:
        intensity = v / 100
        colors.append(f"rgba(45, 212, 191, {0.3 + 0.7 * intensity})")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=skill_counts.values,
        y=skill_counts.index,
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Ofertas: %{x}<extra></extra>",
        text=skill_counts.values,
        textposition="outside",
        textfont={"color": "#94a3b8", "size": 12, "family": _FONT},
        cliponaxis=False,
    ))

    layout = _base_layout(
        f"Top {top_n} Skills Más Demandadas",
        "Número de Ofertas", ""
    )
    layout["yaxis"]["categoryorder"] = "total ascending"
    fig.update_layout(
        **layout,
        xaxis_showgrid=True,
        bargap=0.3,
        uniformtext_minsize=10,
    )
    return fig


def scatter_experiencia_salario(df: pd.DataFrame) -> Any:
    required = ["experiencia_requerida", "salario_promedio", "cargo_nivel"]
    if df.empty or not all(c in df.columns for c in required):
        return _empty_fig()
    level_names = {"tecnico": "Técnico", "tecnologo": "Tecnólogo", "ingeniero": "Ingeniero", "senior": "Senior"}
    dff = df.copy()
    dff["cargo_nivel_label"] = dff["cargo_nivel"].map(level_names).fillna(dff["cargo_nivel"])
    fig = px.scatter(
        dff, x="experiencia_requerida", y="salario_promedio",
        color="cargo_nivel_label",
        title="Experiencia vs Salario Promedio",
        labels={
            "experiencia_requerida": "Años de Experiencia",
            "salario_promedio": "Salario Promedio (COP)",
            "cargo_nivel_label": "Nivel",
        },
        color_discrete_sequence=_COLORS,
        trendline="ols",
        trendline_color_override="rgba(255,255,255,0.25)",
        hover_data={"titulo": True, "empresa": True, "cargo_nivel_label": False},
        opacity=0.75,
        size_max=8,
    )
    fig.update_traces(
        marker={"size": 7, "line": {"width": 0.5, "color": "rgba(0,0,0,0.3)"}},
        selector={"mode": "markers"},
        hovertemplate="<b>%{customdata[0]}</b><br>Empresa: %{customdata[1]}<br>Exp: %{x}a · Salario: $%{y:,.0f}<extra></extra>",
    )
    fig.update_layout(
        **_base_layout(
            "Experiencia vs Salario Promedio",
            "Años de Experiencia", "Salario Promedio (COP)"
        ),
        yaxis_tickformat="$,.0f",
        xaxis_dtick=2,
    )
    return fig


def heatmap_cargo_modalidad(df: pd.DataFrame) -> Any:
    if df.empty or "cargo_nivel" not in df.columns or "modalidad_clean" not in df.columns:
        return _empty_fig()
    level_names = {"tecnico": "Técnico", "tecnologo": "Tecnólogo", "ingeniero": "Ingeniero", "senior": "Senior"}
    modal_names = {"presencial": "Presencial", "hibrido": "Híbrido", "remoto": "Remoto"}
    dff = df.copy()
    dff["nivel"] = dff["cargo_nivel"].map(level_names).fillna(dff["cargo_nivel"])
    dff["modalidad"] = dff["modalidad_clean"].map(modal_names).fillna(dff["modalidad_clean"])
    pivot = dff.pivot_table(
        values="salario_promedio", index="nivel", columns="modalidad",
        aggfunc="mean",
    )
    if pivot.empty:
        return _empty_fig()
    fig = px.imshow(
        pivot, text_auto=",.0f", aspect="auto",
        title="Salario Promedio: Cargo × Modalidad",
        labels={"x": "Modalidad", "y": "Nivel del Cargo", "color": "Salario (COP)"},
        color_continuous_scale=[
            [0, "#0f172a"],
            [0.25, "#1a3a3a"],
            [0.5, "#2dd4bf"],
            [0.75, "#14b8a6"],
            [1, "#0d9488"],
        ],
        zmin=None, zmax=None,
    )
    fig.update_traces(
        hovertemplate="<b>%{x} · %{y}</b><br>Salario: $%{z:,.0f}<extra></extra>",
        textfont={"color": "#e2e8f0", "size": 13, "family": _FONT},
    )
    layout = _base_layout("Salario Promedio: Cargo × Modalidad")
    layout["xaxis"]["side"] = "bottom"
    layout["xaxis"]["tickfont"] = {"size": 13, "color": "#94a3b8"}
    layout["yaxis"]["tickfont"] = {"size": 13, "color": "#94a3b8"}
    fig.update_layout(
        **layout,
        coloraxis_colorbar={
            "title": {"text": "COP", "font": {"size": 11, "color": "#94a3b8"}},
            "tickformat": "$,.0f",
            "tickfont": {"size": 10, "color": "#94a3b8"},
        },
    )
    return fig


def timeline_ofertas(df: pd.DataFrame) -> Any:
    if df.empty or "fecha_publicacion" not in df.columns:
        return _empty_fig()
    dff = df.copy()
    dff["fecha_publicacion"] = pd.to_datetime(dff["fecha_publicacion"], errors="coerce")
    dff = dff.dropna(subset=["fecha_publicacion"])
    if dff.empty:
        return _empty_fig()
    timeline = dff.groupby(dff["fecha_publicacion"].dt.date).size().reset_index(name="count")
    fig = px.area(
        timeline, x="fecha_publicacion", y="count",
        title="Evolución Temporal de Ofertas Publicadas",
        labels={"fecha_publicacion": "Fecha", "count": "Número de Ofertas"},
        color_discrete_sequence=[_PRIMARY],
    )
    fig.update_traces(
        line={"width": 2.5, "color": _PRIMARY},
        hovertemplate="<b>%{x}</b><br>Ofertas: %{y}<extra></extra>",
        fill="tozeroy",
        fillcolor="rgba(87,241,219,0.08)",
    )
    fig.update_layout(
        **_base_layout(
            "Evolución Temporal de Ofertas Publicadas",
            "Fecha", "Número de Ofertas"
        ),
        xaxis_tickformat="%b %Y",
        hovermode="x unified",
        showlegend=False,
    )
    return fig


def salary_by_role(df: pd.DataFrame, selected_roles: list) -> Any:
    if df.empty or "role_categoria" not in df.columns:
        return _empty_fig("Selecciona uno o más roles laborales")
    dff = df[df["role_categoria"].isin(selected_roles)].dropna(subset=["salario_promedio", "role_categoria"])
    if dff.empty:
        return _empty_fig("No hay datos para los roles seleccionados")
    stats = dff.groupby("role_categoria")["salario_promedio"].agg(["mean", "median", "count"]).round(0).reset_index()
    stats.columns = ["role_categoria", "Promedio", "Mediana", "Ofertas"]
    stats = stats.sort_values("Promedio", ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=stats["role_categoria"],
        x=stats["Promedio"],
        orientation="h",
        name="Promedio",
        marker_color=_PRIMARY,
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Promedio: $%{x:,.0f}<br>Ofertas: %{customdata[0]}<extra></extra>",
        customdata=stats[["Ofertas"]],
        text=stats["Promedio"].apply(lambda x: f"${x:,.0f}"),
        textposition="outside",
        textfont={"color": "#94a3b8", "size": 11, "family": _FONT},
        cliponaxis=False,
    ))
    fig.add_trace(go.Scatter(
        y=stats["role_categoria"],
        x=stats["Mediana"],
        mode="markers",
        name="Mediana",
        marker={"color": "#f59e0b", "size": 10, "symbol": "diamond"},
        hovertemplate="<b>%{y}</b><br>Mediana: $%{x:,.0f}<extra></extra>",
    ))
    layout = _base_layout(
        "Salario Promedio por Rol Laboral",
        "Salario (COP)", ""
    )
    layout["yaxis"]["categoryorder"] = "total ascending"
    layout["legend"] = {"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0.5, "xanchor": "center"}
    fig.update_layout(
        **layout,
        xaxis_tickformat="$,.0f",
        bargap=0.35,
    )
    return fig
