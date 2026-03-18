"""
Стоматологическая клиника — Аналитический дашборд
Автор: [Ваше имя]
Платформа: Python 3.11, Plotly Dash 2.x
Библиотеки: dash, plotly, pandas, numpy
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Генерация демо-данных (имитация БД стоматологической клиники)
# ─────────────────────────────────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

DOCTORS = ["Иванов А.П.", "Петрова М.С.", "Сидоров К.В.", "Козлова Н.Е.", "Морозов Р.Д."]
DIAGNOSES = {
    "K02.1": "Кариес дентина",
    "K02.2": "Кариес цемента",
    "K04.0": "Пульпит",
    "K04.7": "Периапикальный абсцесс",
    "K05.1": "Хронический гингивит",
    "K06.0": "Рецессия десны",
    "K08.1": "Потеря зубов вследствие несчастного случая",
    "K08.2": "Атрофия альвеолярного края",
}
STATUSES = ["DONE", "SCHEDULED", "CALLED", "IN_PROGRESS"]
STATUS_WEIGHTS = [0.65, 0.20, 0.08, 0.07]

# Генерируем записи на приёмы за 12 месяцев
start_date = datetime(2024, 1, 1)
n_records = 480

appointments = []
for i in range(n_records):
    date = start_date + timedelta(days=random.randint(0, 365))
    doctor = random.choice(DOCTORS)
    diagnosis_code = random.choice(list(DIAGNOSES.keys()))
    status = random.choices(STATUSES, STATUS_WEIGHTS)[0]
    cost = round(random.uniform(800, 15000), 2)
    teeth_count = random.randint(1, 4)
    appointments.append({
        "id": i + 1,
        "date": date,
        "month": date.strftime("%Y-%m"),
        "month_label": date.strftime("%b %Y"),
        "doctor": doctor,
        "diagnosis_code": diagnosis_code,
        "diagnosis": DIAGNOSES[diagnosis_code],
        "status": status,
        "cost": cost,
        "teeth_count": teeth_count,
        "patient_id": random.randint(1, 120),
    })

df = pd.DataFrame(appointments)
df["date"] = pd.to_datetime(df["date"])
df["quarter"] = df["date"].dt.to_period("Q").astype(str)
df["week"] = df["date"].dt.isocalendar().week

# Материалы
MATERIALS = ["Пломбировочный материал", "Анестетик", "Антисептик", "Коронка", "Имплант", "Брекеты"]
mat_usage = pd.DataFrame({
    "material": MATERIALS,
    "used": [random.randint(50, 300) for _ in MATERIALS],
    "cost_per_unit": [random.uniform(100, 5000) for _ in MATERIALS],
})
mat_usage["total_cost"] = mat_usage["used"] * mat_usage["cost_per_unit"]

# ─────────────────────────────────────────────────────────────────────────────
# KPI-функции
# ─────────────────────────────────────────────────────────────────────────────
def calc_kpis(data):
    total = len(data)
    revenue = data["cost"].sum()
    done = (data["status"] == "DONE").sum()
    patients = data["patient_id"].nunique()
    return total, revenue, done, patients


# ─────────────────────────────────────────────────────────────────────────────
# Инициализация приложения
# ─────────────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    title="Стоматология — Аналитика",
    suppress_callback_exceptions=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Стили (CSS-переменные)
# ─────────────────────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#2563eb",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "bg": "#f0f4ff",
    "card": "#ffffff",
    "text": "#1e293b",
    "muted": "#64748b",
    "border": "#e2e8f0",
}

card_style = {
    "backgroundColor": COLORS["card"],
    "borderRadius": "12px",
    "padding": "20px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.07)",
    "border": f"1px solid {COLORS['border']}",
}

kpi_style = {
    **card_style,
    "textAlign": "center",
    "minWidth": "180px",
    "flex": "1",
}


def kpi_card(title, value, color, icon):
    return html.Div([
        html.Div(icon, style={"fontSize": "28px", "marginBottom": "6px"}),
        html.Div(value, style={"fontSize": "28px", "fontWeight": "700", "color": color}),
        html.Div(title, style={"fontSize": "13px", "color": COLORS["muted"], "marginTop": "4px"}),
    ], style=kpi_style)


# ─────────────────────────────────────────────────────────────────────────────
# Layout
# ─────────────────────────────────────────────────────────────────────────────
app.layout = html.Div([

    # ── Header ──────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span("🦷", style={"fontSize": "36px", "marginRight": "14px"}),
            html.Div([
                html.H1("Стоматологическая клиника",
                        style={"margin": "0", "fontSize": "22px", "fontWeight": "700", "color": "#fff"}),
                html.P("Аналитический дашборд • Plotly Dash",
                       style={"margin": "0", "fontSize": "12px", "color": "rgba(255,255,255,0.75)"}),
            ])
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div(
            datetime.now().strftime("%d %B %Y"),
            style={"color": "rgba(255,255,255,0.8)", "fontSize": "14px"}
        ),
    ], style={
        "background": f"linear-gradient(135deg, {COLORS['primary']}, #1e40af)",
        "padding": "18px 32px",
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "borderRadius": "0 0 16px 16px",
        "boxShadow": "0 4px 16px rgba(37,99,235,0.3)",
    }),

    # ── Фильтры ─────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Label("Врач:", style={"fontWeight": "600", "fontSize": "13px", "color": COLORS["muted"]}),
            dcc.Dropdown(
                id="filter-doctor",
                options=[{"label": "Все врачи", "value": "all"}] +
                        [{"label": d, "value": d} for d in DOCTORS],
                value="all",
                clearable=False,
                style={"minWidth": "200px"},
            ),
        ]),
        html.Div([
            html.Label("Диагноз:", style={"fontWeight": "600", "fontSize": "13px", "color": COLORS["muted"]}),
            dcc.Dropdown(
                id="filter-diagnosis",
                options=[{"label": "Все диагнозы", "value": "all"}] +
                        [{"label": f"{k} — {v}", "value": k} for k, v in DIAGNOSES.items()],
                value="all",
                clearable=False,
                style={"minWidth": "260px"},
            ),
        ]),
        html.Div([
            html.Label("Период:", style={"fontWeight": "600", "fontSize": "13px", "color": COLORS["muted"]}),
            dcc.DatePickerRange(
                id="filter-dates",
                start_date=df["date"].min().date(),
                end_date=df["date"].max().date(),
                display_format="DD.MM.YYYY",
                style={"fontSize": "13px"},
            ),
        ]),
    ], style={
        "display": "flex",
        "gap": "24px",
        "flexWrap": "wrap",
        "alignItems": "flex-end",
        "padding": "20px 32px",
        "backgroundColor": COLORS["card"],
        "borderBottom": f"1px solid {COLORS['border']}",
    }),

    # ── Основное тело ────────────────────────────────────────────────────────
    html.Div([

        # ── KPI-карточки ────────────────────────────────────────────────────
        html.Div(id="kpi-row", style={
            "display": "flex",
            "gap": "16px",
            "flexWrap": "wrap",
            "marginBottom": "20px",
        }),

        # ── Графики: строка 1 ────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H3("Доходы по месяцам", style={"margin": "0 0 12px", "fontSize": "15px", "fontWeight": "600"}),
                dcc.Graph(id="chart-revenue", config={"displayModeBar": False}),
            ], style={**card_style, "flex": "2"}),

            html.Div([
                html.H3("Статусы приёмов", style={"margin": "0 0 12px", "fontSize": "15px", "fontWeight": "600"}),
                dcc.Graph(id="chart-status", config={"displayModeBar": False}),
            ], style={**card_style, "flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px", "flexWrap": "wrap"}),

        # ── Графики: строка 2 ────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H3("Нагрузка по врачам", style={"margin": "0 0 12px", "fontSize": "15px", "fontWeight": "600"}),
                dcc.Graph(id="chart-doctors", config={"displayModeBar": False}),
            ], style={**card_style, "flex": "1"}),

            html.Div([
                html.H3("Топ диагнозов", style={"margin": "0 0 12px", "fontSize": "15px", "fontWeight": "600"}),
                dcc.Graph(id="chart-diagnoses", config={"displayModeBar": False}),
            ], style={**card_style, "flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px", "flexWrap": "wrap"}),

        # ── Графики: строка 3 ────────────────────────────────────────────────
        html.Div([
            html.Div([
                html.H3("Тепловая карта: приёмы по дням недели",
                        style={"margin": "0 0 12px", "fontSize": "15px", "fontWeight": "600"}),
                dcc.Graph(id="chart-heatmap", config={"displayModeBar": False}),
            ], style={**card_style, "flex": "2"}),

            html.Div([
                html.H3("Использование материалов",
                        style={"margin": "0 0 12px", "fontSize": "15px", "fontWeight": "600"}),
                dcc.Graph(id="chart-materials", config={"displayModeBar": False}),
            ], style={**card_style, "flex": "1"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px", "flexWrap": "wrap"}),

        # ── Scatter: стоимость vs количество зубов ───────────────────────────
        html.Div([
            html.H3("Стоимость приёма vs количество зубов",
                    style={"margin": "0 0 12px", "fontSize": "15px", "fontWeight": "600"}),
            dcc.Graph(id="chart-scatter", config={"displayModeBar": False}),
        ], style={**card_style, "marginBottom": "20px"}),

        # ── Таблица последних записей ────────────────────────────────────────
        html.Div([
            html.H3("Последние записи", style={"margin": "0 0 14px", "fontSize": "15px", "fontWeight": "600"}),
            html.Div(id="table-appointments"),
        ], style=card_style),

    ], style={"padding": "24px 32px", "backgroundColor": COLORS["bg"], "minHeight": "100vh"}),

    # Footer
    html.Div([
        html.P("Стоматологическая клиника — Аналитический дашборд | Python + Plotly Dash",
               style={"margin": "0", "color": COLORS["muted"], "fontSize": "12px", "textAlign": "center"}),
    ], style={"padding": "16px", "borderTop": f"1px solid {COLORS['border']}"}),

], style={"fontFamily": "'Segoe UI', Arial, sans-serif", "backgroundColor": COLORS["bg"]})


# ─────────────────────────────────────────────────────────────────────────────
# Callbacks
# ─────────────────────────────────────────────────────────────────────────────
def filter_data(doctor, diagnosis, start_date, end_date):
    data = df.copy()
    if doctor != "all":
        data = data[data["doctor"] == doctor]
    if diagnosis != "all":
        data = data[data["diagnosis_code"] == diagnosis]
    if start_date and end_date:
        data = data[(data["date"] >= start_date) & (data["date"] <= end_date)]
    return data


@app.callback(
    Output("kpi-row", "children"),
    Output("chart-revenue", "figure"),
    Output("chart-status", "figure"),
    Output("chart-doctors", "figure"),
    Output("chart-diagnoses", "figure"),
    Output("chart-heatmap", "figure"),
    Output("chart-materials", "figure"),
    Output("chart-scatter", "figure"),
    Output("table-appointments", "children"),
    Input("filter-doctor", "value"),
    Input("filter-diagnosis", "value"),
    Input("filter-dates", "start_date"),
    Input("filter-dates", "end_date"),
)
def update_all(doctor, diagnosis, start_date, end_date):
    data = filter_data(doctor, diagnosis, start_date, end_date)

    # ── KPI ─────────────────────────────────────────────────────────────────
    total, revenue, done, patients = calc_kpis(data)
    kpi_cards = [
        kpi_card("Всего приёмов", str(total), COLORS["primary"], "📅"),
        kpi_card("Выручка (₽)", f"{revenue:,.0f}".replace(",", " "), COLORS["success"], "💰"),
        kpi_card("Завершено", str(done), COLORS["warning"], "✅"),
        kpi_card("Уникальных пациентов", str(patients), COLORS["danger"], "👥"),
    ]

    # ── График 1: доходы по месяцам ─────────────────────────────────────────
    monthly = data.groupby("month")["cost"].sum().reset_index().sort_values("month")
    monthly["month_label"] = pd.to_datetime(monthly["month"]).dt.strftime("%b %Y")

    fig_revenue = go.Figure()
    fig_revenue.add_trace(go.Bar(
        x=monthly["month_label"], y=monthly["cost"],
        marker_color=COLORS["primary"],
        marker_line_width=0,
        name="Выручка",
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} ₽<extra></extra>",
    ))
    fig_revenue.add_trace(go.Scatter(
        x=monthly["month_label"], y=monthly["cost"],
        mode="lines+markers",
        line=dict(color=COLORS["warning"], width=2),
        marker=dict(size=6),
        name="Тренд",
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} ₽<extra></extra>",
    ))
    fig_revenue.update_layout(**_layout(height=300))

    # ── График 2: статусы (donut) ────────────────────────────────────────────
    status_counts = data["status"].value_counts()
    STATUS_RU = {"DONE": "Завершён", "SCHEDULED": "Запланирован", "CALLED": "Вызван", "IN_PROGRESS": "В процессе"}
    STATUS_COLORS = [COLORS["success"], COLORS["primary"], COLORS["warning"], COLORS["danger"]]
    fig_status = go.Figure(go.Pie(
        labels=[STATUS_RU.get(s, s) for s in status_counts.index],
        values=status_counts.values,
        hole=0.55,
        marker_colors=STATUS_COLORS[:len(status_counts)],
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} приёмов (%{percent})<extra></extra>",
    ))
    fig_status.update_layout(**_layout(height=300))

    # ── График 3: нагрузка по врачам ────────────────────────────────────────
    doc_stats = data.groupby("doctor").agg(
        count=("id", "count"), revenue=("cost", "sum")
    ).sort_values("count", ascending=True).reset_index()

    fig_doctors = go.Figure()
    fig_doctors.add_trace(go.Bar(
        y=doc_stats["doctor"], x=doc_stats["count"],
        orientation="h",
        marker_color=COLORS["primary"],
        name="Приёмы",
        hovertemplate="<b>%{y}</b><br>Приёмов: %{x}<extra></extra>",
    ))
    fig_doctors.update_layout(**_layout(height=300))

    # ── График 4: топ диагнозов ──────────────────────────────────────────────
    diag_counts = data.groupby("diagnosis_code").size().reset_index(name="count")
    diag_counts["label"] = diag_counts["diagnosis_code"].map(DIAGNOSES)
    diag_counts = diag_counts.sort_values("count", ascending=False).head(6)

    fig_diagnoses = go.Figure(go.Bar(
        x=diag_counts["count"], y=diag_counts["diagnosis_code"],
        orientation="h",
        marker_color=px.colors.sequential.Blues_r[:len(diag_counts)],
        text=diag_counts["count"],
        textposition="outside",
        hovertext=diag_counts["label"],
        hovertemplate="<b>%{hovertext}</b><br>Кол-во: %{x}<extra></extra>",
    ))
    fig_diagnoses.update_layout(**_layout(height=300))

    # ── График 5: тепловая карта ─────────────────────────────────────────────
    data2 = data.copy()
    data2["dow"] = data2["date"].dt.dayofweek
    data2["month_n"] = data2["date"].dt.month
    heat = data2.groupby(["month_n", "dow"]).size().reset_index(name="count")
    heat_pivot = heat.pivot(index="dow", columns="month_n", values="count").fillna(0)

    DOW = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    MONTHS = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
              "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]

    fig_heatmap = go.Figure(go.Heatmap(
        z=heat_pivot.values,
        x=[MONTHS[m - 1] for m in heat_pivot.columns],
        y=[DOW[d] for d in heat_pivot.index],
        colorscale="Blues",
        hovertemplate="<b>%{y}, %{x}</b><br>Приёмов: %{z}<extra></extra>",
    ))
    fig_heatmap.update_layout(**_layout(height=280))

    # ── График 6: материалы (горизонт. бар) ─────────────────────────────────
    mat_sorted = mat_usage.sort_values("used", ascending=True)
    fig_materials = go.Figure(go.Bar(
        y=mat_sorted["material"], x=mat_sorted["used"],
        orientation="h",
        marker_color=COLORS["success"],
        hovertemplate="<b>%{y}</b><br>Использовано: %{x} ед.<extra></extra>",
    ))
    fig_materials.update_layout(**_layout(height=300))

    # ── График 7: scatter ────────────────────────────────────────────────────
    fig_scatter = px.scatter(
        data, x="teeth_count", y="cost",
        color="doctor",
        size="cost",
        size_max=18,
        labels={"teeth_count": "Количество зубов", "cost": "Стоимость (₽)", "doctor": "Врач"},
        hover_data={"diagnosis": True, "status": True},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_scatter.update_layout(**_layout(height=340))

    # ── Таблица ───────────────────────────────────────────────────────────────
    table_data = data.sort_values("date", ascending=False).head(20).copy()
    table_data["date_str"] = table_data["date"].dt.strftime("%d.%m.%Y")
    table_data["cost_str"] = table_data["cost"].apply(lambda x: f"{x:,.0f} ₽".replace(",", " "))
    STATUS_BADGE = {
        "DONE": "✅ Завершён", "SCHEDULED": "🗓 Запланирован",
        "CALLED": "📢 Вызван", "IN_PROGRESS": "⚙️ В процессе",
    }
    table_data["status_ru"] = table_data["status"].map(STATUS_BADGE)

    table = dash_table.DataTable(
        data=table_data[["date_str", "doctor", "diagnosis", "status_ru", "cost_str", "teeth_count"]].to_dict("records"),
        columns=[
            {"name": "Дата", "id": "date_str"},
            {"name": "Врач", "id": "doctor"},
            {"name": "Диагноз", "id": "diagnosis"},
            {"name": "Статус", "id": "status_ru"},
            {"name": "Стоимость", "id": "cost_str"},
            {"name": "Зубов", "id": "teeth_count"},
        ],
        style_table={"overflowX": "auto"},
        style_cell={
            "fontFamily": "'Segoe UI', Arial, sans-serif",
            "fontSize": "13px",
            "padding": "10px 12px",
            "border": "1px solid #e2e8f0",
            "textAlign": "left",
        },
        style_header={
            "backgroundColor": "#f8fafc",
            "fontWeight": "700",
            "color": COLORS["text"],
            "border": "1px solid #e2e8f0",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#fafcff"},
        ],
        page_size=10,
        sort_action="native",
    )

    return kpi_cards, fig_revenue, fig_status, fig_doctors, fig_diagnoses, fig_heatmap, fig_materials, fig_scatter, table


def _layout(height=300):
    return dict(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Segoe UI', Arial, sans-serif", size=12, color=COLORS["text"]),
        xaxis=dict(gridcolor="#f1f5f9", gridwidth=1),
        yaxis=dict(gridcolor="#f1f5f9", gridwidth=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=8050, host="0.0.0.0",)
