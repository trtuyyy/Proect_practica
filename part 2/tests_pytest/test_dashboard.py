"""
Задание 2 — Тестирование дашборда стоматологической клиники
Инструмент: pytest (unit-тесты логики и данных)
Платформа: Python 3.11 + pytest 8.x
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import sys
import os

# ─── Импортируем логику из app.py (или дублируем её) ────────────────────────
# Если app.py лежит рядом, можно: sys.path.insert(0, '..')
# Для автономности тестов дублируем генерацию данных здесь.

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
    "K08.1": "Потеря зубов",
    "K08.2": "Атрофия альвеолярного края",
}
STATUSES = ["DONE", "SCHEDULED", "CALLED", "IN_PROGRESS"]
STATUS_WEIGHTS = [0.65, 0.20, 0.08, 0.07]


def generate_appointments(n=480, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    start = datetime(2024, 1, 1)
    rows = []
    for i in range(n):
        date = start + timedelta(days=random.randint(0, 365))
        rows.append({
            "id": i + 1,
            "date": date,
            "month": date.strftime("%Y-%m"),
            "doctor": random.choice(DOCTORS),
            "diagnosis_code": random.choice(list(DIAGNOSES.keys())),
            "status": random.choices(STATUSES, STATUS_WEIGHTS)[0],
            "cost": round(random.uniform(800, 15000), 2),
            "teeth_count": random.randint(1, 4),
            "patient_id": random.randint(1, 120),
        })
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def calc_kpis(data):
    return {
        "total": len(data),
        "revenue": round(data["cost"].sum(), 2),
        "done": int((data["status"] == "DONE").sum()),
        "patients": data["patient_id"].nunique(),
    }


def filter_data(df, doctor="all", diagnosis="all", start_date=None, end_date=None):
    data = df.copy()
    if doctor != "all":
        data = data[data["doctor"] == doctor]
    if diagnosis != "all":
        data = data[data["diagnosis_code"] == diagnosis]
    if start_date:
        data = data[data["date"] >= pd.Timestamp(start_date)]
    if end_date:
        data = data[data["date"] <= pd.Timestamp(end_date)]
    return data


# ─── Фикстуры ────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def df():
    return generate_appointments(480)


@pytest.fixture(scope="module")
def kpis(df):
    return calc_kpis(df)


# ════════════════════════════════════════════════════════════════════════════════
# 1. ТЕСТЫ ГЕНЕРАЦИИ ДАННЫХ
# ════════════════════════════════════════════════════════════════════════════════
class TestDataGeneration:

    def test_dataframe_not_empty(self, df):
        """DataFrame не пустой"""
        assert len(df) == 480

    def test_required_columns_exist(self, df):
        """Все обязательные столбцы присутствуют"""
        required = ["id", "date", "doctor", "diagnosis_code", "status", "cost",
                    "teeth_count", "patient_id", "month"]
        for col in required:
            assert col in df.columns, f"Отсутствует столбец: {col}"

    def test_no_null_values(self, df):
        """Нет пропущенных значений в ключевых полях"""
        for col in ["id", "date", "doctor", "status", "cost"]:
            assert df[col].isnull().sum() == 0, f"Есть NULL в столбце {col}"

    def test_date_column_is_datetime(self, df):
        """Столбец date является типом datetime"""
        assert pd.api.types.is_datetime64_any_dtype(df["date"])

    def test_cost_range(self, df):
        """Стоимость приёма в допустимом диапазоне (800–15000)"""
        assert df["cost"].min() >= 800
        assert df["cost"].max() <= 15000

    def test_teeth_count_range(self, df):
        """Количество зубов в диапазоне 1–4"""
        assert df["teeth_count"].min() >= 1
        assert df["teeth_count"].max() <= 4

    def test_all_doctors_present(self, df):
        """Все врачи присутствуют в данных"""
        doctors_in_data = set(df["doctor"].unique())
        for doc in DOCTORS:
            assert doc in doctors_in_data, f"Врач {doc} отсутствует в данных"

    def test_all_statuses_valid(self, df):
        """Все статусы из допустимого списка"""
        invalid = set(df["status"].unique()) - set(STATUSES)
        assert len(invalid) == 0, f"Недопустимые статусы: {invalid}"

    def test_all_diagnosis_codes_valid(self, df):
        """Все коды диагнозов из справочника МКБ-10"""
        invalid = set(df["diagnosis_code"].unique()) - set(DIAGNOSES.keys())
        assert len(invalid) == 0, f"Недопустимые коды: {invalid}"

    def test_patient_ids_positive(self, df):
        """ID пациентов положительные"""
        assert (df["patient_id"] > 0).all()

    def test_unique_appointment_ids(self, df):
        """Каждый приём имеет уникальный ID"""
        assert df["id"].nunique() == len(df)


# ════════════════════════════════════════════════════════════════════════════════
# 2. ТЕСТЫ KPI-МЕТРИК
# ════════════════════════════════════════════════════════════════════════════════
class TestKPICalculations:

    def test_total_count(self, df, kpis):
        """KPI: общее количество приёмов совпадает с размером DataFrame"""
        assert kpis["total"] == len(df)

    def test_revenue_positive(self, kpis):
        """KPI: выручка больше нуля"""
        assert kpis["revenue"] > 0

    def test_revenue_matches_sum(self, df, kpis):
        """KPI: выручка совпадает с ручным подсчётом"""
        assert abs(kpis["revenue"] - df["cost"].sum()) < 0.01

    def test_done_count_correct(self, df, kpis):
        """KPI: количество завершённых приёмов корректно"""
        expected = (df["status"] == "DONE").sum()
        assert kpis["done"] == expected

    def test_done_count_leq_total(self, kpis):
        """KPI: завершённых не больше, чем всего приёмов"""
        assert kpis["done"] <= kpis["total"]

    def test_patients_positive(self, kpis):
        """KPI: уникальных пациентов больше нуля"""
        assert kpis["patients"] > 0

    def test_patients_leq_total(self, df, kpis):
        """KPI: пациентов не больше, чем приёмов"""
        assert kpis["patients"] <= kpis["total"]

    def test_kpi_on_empty_dataframe(self):
        """KPI: корректная работа на пустом DataFrame"""
        empty = pd.DataFrame(columns=["id", "date", "doctor", "status",
                                       "cost", "teeth_count", "patient_id"])
        empty["cost"] = pd.Series(dtype=float)
        empty["status"] = pd.Series(dtype=str)
        empty["patient_id"] = pd.Series(dtype=int)
        kpis = calc_kpis(empty)
        assert kpis["total"] == 0
        assert kpis["revenue"] == 0.0
        assert kpis["done"] == 0
        assert kpis["patients"] == 0


# ════════════════════════════════════════════════════════════════════════════════
# 3. ТЕСТЫ ФИЛЬТРАЦИИ
# ════════════════════════════════════════════════════════════════════════════════
class TestFiltering:

    def test_filter_by_doctor(self, df):
        """Фильтр по врачу возвращает только его записи"""
        doctor = DOCTORS[0]
        filtered = filter_data(df, doctor=doctor)
        assert (filtered["doctor"] == doctor).all()
        assert len(filtered) > 0

    def test_filter_all_doctors(self, df):
        """Фильтр 'all' возвращает все записи"""
        filtered = filter_data(df, doctor="all")
        assert len(filtered) == len(df)

    def test_filter_by_diagnosis(self, df):
        """Фильтр по диагнозу возвращает только нужные записи"""
        code = "K04.0"
        filtered = filter_data(df, diagnosis=code)
        assert (filtered["diagnosis_code"] == code).all()
        assert len(filtered) > 0

    def test_filter_by_date_range(self, df):
        """Фильтр по датам работает корректно"""
        filtered = filter_data(df,
                               start_date="2024-03-01",
                               end_date="2024-05-31")
        assert (filtered["date"] >= "2024-03-01").all()
        assert (filtered["date"] <= "2024-05-31").all()

    def test_filter_combination(self, df):
        """Комбинированный фильтр: врач + диагноз"""
        doctor = DOCTORS[1]
        code = "K02.1"
        filtered = filter_data(df, doctor=doctor, diagnosis=code)
        if len(filtered) > 0:
            assert (filtered["doctor"] == doctor).all()
            assert (filtered["diagnosis_code"] == code).all()

    def test_filter_nonexistent_doctor(self, df):
        """Фильтр по несуществующему врачу возвращает пустой DataFrame"""
        filtered = filter_data(df, doctor="Несуществующий В.В.")
        assert len(filtered) == 0

    def test_filter_narrow_date_range(self, df):
        """Узкий диапазон дат возвращает меньше записей"""
        full = filter_data(df)
        narrow = filter_data(df, start_date="2024-06-01", end_date="2024-06-30")
        assert len(narrow) <= len(full)

    def test_filter_does_not_mutate_original(self, df):
        """Фильтрация не изменяет исходный DataFrame"""
        original_len = len(df)
        _ = filter_data(df, doctor=DOCTORS[0])
        assert len(df) == original_len


# ════════════════════════════════════════════════════════════════════════════════
# 4. ТЕСТЫ АГРЕГАЦИЙ (для графиков)
# ════════════════════════════════════════════════════════════════════════════════
class TestAggregations:

    def test_monthly_revenue_groupby(self, df):
        """Группировка по месяцам работает корректно"""
        monthly = df.groupby("month")["cost"].sum()
        assert monthly.sum() == pytest.approx(df["cost"].sum(), rel=1e-6)

    def test_status_counts_sum_to_total(self, df):
        """Сумма по статусам равна общему количеству"""
        status_counts = df["status"].value_counts()
        assert status_counts.sum() == len(df)

    def test_all_statuses_in_counts(self, df):
        """Все четыре статуса присутствуют в данных"""
        counts = df["status"].value_counts()
        for s in STATUSES:
            assert s in counts.index, f"Статус {s} отсутствует"

    def test_top_diagnoses_limited(self, df):
        """Топ диагнозов содержит не более 6 записей"""
        top = df["diagnosis_code"].value_counts().head(6)
        assert len(top) <= 6

    def test_doctor_aggregation_covers_all(self, df):
        """Агрегация по врачам охватывает всех врачей"""
        doc_counts = df.groupby("doctor").size()
        assert set(doc_counts.index) == set(DOCTORS)

    def test_heatmap_pivot_shape(self, df):
        """Тепловая карта: pivot корректной формы"""
        df2 = df.copy()
        df2["dow"] = df2["date"].dt.dayofweek
        df2["month_n"] = df2["date"].dt.month
        heat = df2.groupby(["dow", "month_n"]).size().reset_index(name="count")
        pivot = heat.pivot(index="dow", columns="month_n", values="count").fillna(0)
        assert pivot.shape[0] <= 7   # дней недели не более 7
        assert pivot.shape[1] <= 12  # месяцев не более 12

    def test_scatter_data_integrity(self, df):
        """Scatter: данные для точечной диаграммы корректны"""
        assert "teeth_count" in df.columns
        assert "cost" in df.columns
        assert "doctor" in df.columns
        assert df["teeth_count"].dtype in [np.int64, np.int32, int]
        assert df["cost"].dtype in [np.float64, float]


# ════════════════════════════════════════════════════════════════════════════════
# 5. ТЕСТЫ БИЗНЕС-ПРАВИЛ (предметная область ВКР)
# ════════════════════════════════════════════════════════════════════════════════
class TestBusinessRules:

    def test_done_appointments_have_positive_cost(self, df):
        """Завершённые приёмы имеют положительную стоимость"""
        done = df[df["status"] == "DONE"]
        assert (done["cost"] > 0).all()

    def test_teeth_count_positive(self, df):
        """Количество зубов в приёме всегда положительное"""
        assert (df["teeth_count"] > 0).all()

    def test_done_ratio(self, df):
        """Доля завершённых приёмов разумная (> 50%)"""
        ratio = (df["status"] == "DONE").mean()
        assert ratio > 0.5, f"Доля DONE слишком мала: {ratio:.2%}"

    def test_average_cost_in_range(self, df):
        """Средняя стоимость приёма в ожидаемом диапазоне"""
        avg = df["cost"].mean()
        assert 1000 < avg < 14000, f"Средняя стоимость вне диапазона: {avg:.2f}"

    def test_diagnosis_codes_match_mkb10_pattern(self, df):
        """Коды диагнозов соответствуют шаблону МКБ-10 (буква + цифры)"""
        import re
        pattern = re.compile(r'^[A-Z]\d{2}(\.\d)?$')
        for code in df["diagnosis_code"].unique():
            assert pattern.match(code), f"Код {code} не соответствует МКБ-10"

    def test_no_future_appointments(self, df):
        """Нет приёмов в будущем (относительно 2024)"""
        assert (df["date"] <= pd.Timestamp("2025-01-01")).all()

    def test_revenue_per_doctor_positive(self, df):
        """Выручка каждого врача положительная"""
        revenue_by_doc = df.groupby("doctor")["cost"].sum()
        assert (revenue_by_doc > 0).all()
