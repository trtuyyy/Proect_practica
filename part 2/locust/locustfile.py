"""
Задание 2 — Нагрузочное тестирование дашборда стоматологической клиники
Инструмент: Locust 2.29.0
Платформа: Python 3.12

Запуск (web UI):
    locust -f locust/locustfile.py --host=http://localhost:8050

Запуск (headless):
    locust -f locust/locustfile.py --host=http://localhost:8050 \
           --headless -u 50 -r 10 --run-time 60s \
           --html locust/report_locust.html
"""

from locust import HttpUser, task, between, events
import json
import random
import logging

logger = logging.getLogger(__name__)

DOCTORS    = ["Иванов А.П.", "Петрова М.С.", "Сидоров К.В.", "Козлова Н.Е.", "Морозов Р.Д."]
DIAGNOSES  = ["K02.1", "K02.2", "K04.0", "K04.7", "K05.1", "K06.0", "K08.1", "K08.2"]
DATE_PAIRS = [
    ("2024-01-01", "2024-03-31"),
    ("2024-04-01", "2024-06-30"),
    ("2024-07-01", "2024-09-30"),
    ("2024-01-01", "2024-12-31"),
]

# ─── Правильный payload для Dash 2.x ─────────────────────────────────────────
# Dash 2.x ожидает формат:
# {
#   "output": "component-id.property",
#   "outputs": {"id": "...", "property": "..."},   <- для одного output
#   "inputs": [...],
#   "changedPropIds": [...],
#   "state": []
# }
# Для множественных outputs используется список в "outputs"

def make_callback_payload(doctor="all", diagnosis="all",
                          start_date="2024-01-01", end_date="2024-12-31",
                          changed="filter-doctor.value"):
    """Формирует корректный payload для /_dash-update-component (Dash 2.x)"""
    return {
        "output": (
            "kpi-row.children.."
            "chart-revenue.figure.."
            "chart-status.figure.."
            "chart-doctors.figure.."
            "chart-diagnoses.figure.."
            "chart-heatmap.figure.."
            "chart-materials.figure.."
            "chart-scatter.figure.."
            "table-appointments.children"
        ),
        "outputs": [
            {"id": "kpi-row",              "property": "children"},
            {"id": "chart-revenue",        "property": "figure"},
            {"id": "chart-status",         "property": "figure"},
            {"id": "chart-doctors",        "property": "figure"},
            {"id": "chart-diagnoses",      "property": "figure"},
            {"id": "chart-heatmap",        "property": "figure"},
            {"id": "chart-materials",      "property": "figure"},
            {"id": "chart-scatter",        "property": "figure"},
            {"id": "table-appointments",   "property": "children"},
        ],
        "inputs": [
            {"id": "filter-doctor",    "property": "value",      "value": doctor},
            {"id": "filter-diagnosis", "property": "value",      "value": diagnosis},
            {"id": "filter-dates",     "property": "start_date", "value": start_date},
            {"id": "filter-dates",     "property": "end_date",   "value": end_date},
        ],
        "changedPropIds": [changed],
        "state": [],
    }


# ════════════════════════════════════════════════════════════════════════════════
# Пользователь А: пассивный просмотр (60%)
# ════════════════════════════════════════════════════════════════════════════════
class DashboardViewer(HttpUser):
    """Открывает страницу и листает без фильтров."""
    weight    = 3
    wait_time = between(2, 5)

    @task(5)
    def load_main_page(self):
        with self.client.get("/", catch_response=True, name="GET /") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Ошибка {r.status_code}")

    @task(3)
    def load_dash_layout(self):
        with self.client.get("/_dash-layout", catch_response=True,
                             name="GET /_dash-layout") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Layout недоступен: {r.status_code}")

    @task(2)
    def load_dash_dependencies(self):
        with self.client.get("/_dash-dependencies", catch_response=True,
                             name="GET /_dash-dependencies") as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Dependencies недоступны: {r.status_code}")


# ════════════════════════════════════════════════════════════════════════════════
# Пользователь Б: активная фильтрация (30%)
# ════════════════════════════════════════════════════════════════════════════════
class FilteringUser(HttpUser):
    """Активно применяет фильтры — отправляет POST callback."""
    weight    = 2
    wait_time = between(1, 3)

    def on_start(self):
        self.client.get("/")

    @task(4)
    def filter_by_doctor(self):
        doctor  = random.choice(DOCTORS + ["all"])
        payload = make_callback_payload(
            doctor=doctor,
            changed="filter-doctor.value",
        )
        with self.client.post(
            "/_dash-update-component",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="POST callback:filter_doctor",
        ) as r:
            if r.status_code == 200:
                r.success()
            elif r.status_code == 204:
                r.success()   # Dash иногда отвечает 204 No Content
            else:
                r.failure(f"Callback ошибка: {r.status_code} — {r.text[:120]}")

    @task(3)
    def filter_by_diagnosis(self):
        diagnosis = random.choice(DIAGNOSES + ["all"])
        payload   = make_callback_payload(
            diagnosis=diagnosis,
            changed="filter-diagnosis.value",
        )
        with self.client.post(
            "/_dash-update-component",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="POST callback:filter_diagnosis",
        ) as r:
            if r.status_code in (200, 204):
                r.success()
            else:
                r.failure(f"Callback ошибка: {r.status_code} — {r.text[:120]}")

    @task(2)
    def filter_by_dates(self):
        start, end = random.choice(DATE_PAIRS)
        payload    = make_callback_payload(
            start_date=start,
            end_date=end,
            changed="filter-dates.start_date",
        )
        with self.client.post(
            "/_dash-update-component",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="POST callback:filter_dates",
        ) as r:
            if r.status_code in (200, 204):
                r.success()
            else:
                r.failure(f"Callback ошибка: {r.status_code} — {r.text[:120]}")

    @task(1)
    def reload_page(self):
        self.client.get("/", name="GET page:reload")


# ════════════════════════════════════════════════════════════════════════════════
# Пользователь В: стресс-тест (10%)
# ════════════════════════════════════════════════════════════════════════════════
class StressUser(HttpUser):
    """Быстрые последовательные запросы — пиковая нагрузка."""
    weight    = 1
    wait_time = between(0.1, 0.5)

    @task(2)
    def rapid_main(self):
        self.client.get("/", name="GET stress:main")

    @task(1)
    def rapid_layout(self):
        self.client.get("/_dash-layout", name="GET stress:layout")


# ════════════════════════════════════════════════════════════════════════════════
# Хуки
# ════════════════════════════════════════════════════════════════════════════════
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("=" * 60)
    logger.info("Нагрузочное тестирование — Стоматологический дашборд")
    logger.info("Целевой URL: http://localhost:8050")
    logger.info("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    logger.info("=" * 60)
    logger.info("РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
    logger.info(f"Всего запросов:    {stats.num_requests}")
    logger.info(f"Ошибок:            {stats.num_failures}")
    logger.info(f"Ср. время отклика: {stats.avg_response_time:.1f} мс")
    logger.info(f"Макс. отклик:      {stats.max_response_time:.1f} мс")
    logger.info(f"RPS:               {stats.current_rps:.1f}")
    logger.info("=" * 60)
