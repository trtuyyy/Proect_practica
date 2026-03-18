"""
Задание 2 — E2E тестирование дашборда стоматологической клиники
Инструмент: Playwright (playwright-python)
Платформа: Python 3.12 + playwright 1.44

Запуск:
    python app.py                          # в первом терминале
    pytest tests_playwright/ -v            # во втором терминале
    pytest tests_playwright/ -v --headed   # с видимым браузером
"""

import pytest
from playwright.sync_api import Page, expect
import re

BASE_URL = "http://localhost:8050"


# ─── Фикстуры ────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "locale": "ru-RU",
    }


@pytest.fixture(autouse=True)
def goto_dashboard(page: Page):
    """Перед каждым тестом открываем дашборд и ждём загрузки"""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2500)


def has_dash_error(page: Page) -> bool:
    """
    Проверяет наличие НАСТОЯЩЕЙ ошибки Dash (красный алерт),
    а не просто слово 'Error' в DevTools или других местах.
    """
    dash_error = page.locator(".dash-debug-alert, [data-dash-error], .show-hide-error")
    return dash_error.count() > 0


# ════════════════════════════════════════════════════════════════════════════════
# 1. ТЕСТЫ ЗАГРУЗКИ СТРАНИЦЫ
# ════════════════════════════════════════════════════════════════════════════════
class TestPageLoad:

    def test_page_title(self, page: Page):
        """Заголовок вкладки браузера содержит 'Стоматология'"""
        expect(page).to_have_title(re.compile("Стоматология"))

    def test_header_visible(self, page: Page):
        """Шапка (h1) приложения отображается"""
        # FIX: было locator("text=...") — находил 2 элемента (h1 + footer p)
        header = page.locator("h1", has_text="Стоматологическая клиника").first
        expect(header).to_be_visible()

    def test_dash_logo_emoji_visible(self, page: Page):
        """Логотип 🦷 отображается в шапке"""
        logo = page.locator("text=🦷").first
        expect(logo).to_be_visible()

    def test_no_dash_errors(self, page: Page):
        """Нет всплывающих ошибок Dash (красный алерт)"""
        # FIX: было locator("text=Error") — слово 'Error' есть в DevTools
        assert not has_dash_error(page), "Обнаружена ошибка Dash на странице"

    def test_page_fully_rendered(self, page: Page):
        """Страница полностью отрисована (нет индикаторов загрузки)"""
        loading = page.locator("._dash-loading")
        expect(loading).to_have_count(0)

    def test_kpi_row_exists(self, page: Page):
        """Контейнер KPI-карточек существует и не пустой"""
        kpi_row = page.locator("#kpi-row")
        expect(kpi_row).to_be_visible()
        assert len(kpi_row.inner_text()) > 0


# ════════════════════════════════════════════════════════════════════════════════
# 2. ТЕСТЫ KPI-КАРТОЧЕК
# ════════════════════════════════════════════════════════════════════════════════
class TestKPICards:

    def test_kpi_appointments_visible(self, page: Page):
        """KPI 'Всего приёмов' отображается"""
        card = page.locator("#kpi-row", has_text="Всего приёмов")
        expect(card).to_be_visible()

    def test_kpi_revenue_visible(self, page: Page):
        """KPI 'Выручка (₽)' отображается"""
        # FIX: было locator("text=Выручка") — 2 элемента: KPI div + SVG text в графике
        card = page.locator("#kpi-row div", has_text="Выручка (₽)").first
        expect(card).to_be_visible()

    def test_kpi_done_visible(self, page: Page):
        """KPI 'Завершено' отображается"""
        card = page.locator("#kpi-row", has_text="Завершено")
        expect(card).to_be_visible()

    def test_kpi_patients_visible(self, page: Page):
        """KPI 'Уникальных пациентов' отображается"""
        card = page.locator("#kpi-row", has_text="Уникальных пациентов")
        expect(card).to_be_visible()

    def test_kpi_values_are_numbers(self, page: Page):
        """KPI отображают числовые значения"""
        kpi_row = page.locator("#kpi-row")
        expect(kpi_row).to_be_visible()
        content = kpi_row.inner_text()
        assert any(char.isdigit() for char in content), "В KPI нет числовых значений"

    def test_four_kpi_cards_present(self, page: Page):
        """В KPI-блоке присутствуют все 4 карточки"""
        kpi_text = page.locator("#kpi-row").inner_text()
        for label in ["Всего приёмов", "Выручка", "Завершено", "Уникальных пациентов"]:
            assert label in kpi_text, f"KPI '{label}' не найден"


# ════════════════════════════════════════════════════════════════════════════════
# 3. ТЕСТЫ ФИЛЬТРОВ
# ════════════════════════════════════════════════════════════════════════════════
class TestFilters:

    def test_doctor_dropdown_exists(self, page: Page):
        """Dropdown 'Врач' присутствует на странице"""
        expect(page.locator("#filter-doctor")).to_be_visible()

    def test_diagnosis_dropdown_exists(self, page: Page):
        """Dropdown 'Диагноз' присутствует на странице"""
        expect(page.locator("#filter-diagnosis")).to_be_visible()

    def test_date_picker_exists(self, page: Page):
        """DatePicker присутствует на странице"""
        expect(page.locator("#filter-dates")).to_be_visible()

    def test_doctor_filter_has_all_option(self, page: Page):
        """Dropdown врача содержит опцию 'Все врачи'"""
        # FIX: было page.click("#filter-doctor input") — в Dash 2.x нет <input> внутри Dropdown
        page.locator("#filter-doctor").click()
        page.wait_for_timeout(600)
        page.wait_for_selector("text=Все врачи", timeout=3000)
        expect(page.locator("text=Все врачи").first).to_be_visible()
        page.keyboard.press("Escape")

    def test_doctor_filter_updates_charts(self, page: Page):
        """Выбор врача обновляет графики без ошибок"""
        # FIX: кликаем на контейнер, а не на #filter-doctor input
        page.locator("#filter-doctor").click()
        page.wait_for_timeout(600)
        options = page.locator("[class*='option']")
        if options.count() >= 2:
            options.nth(1).click()
        else:
            page.keyboard.press("Escape")
            return
        page.wait_for_timeout(3000)
        assert not has_dash_error(page), "После смены врача появилась ошибка Dash"

    def test_diagnosis_filter_clickable(self, page: Page):
        """Dropdown диагноза открывается по клику"""
        # FIX: класс .Select-menu-outer устарел в Dash 2.x
        page.locator("#filter-diagnosis").click()
        page.wait_for_timeout(600)
        page.wait_for_selector("text=Все диагнозы", timeout=3000)
        expect(page.locator("text=Все диагнозы").first).to_be_visible()
        page.keyboard.press("Escape")

    def test_filter_reset_to_all(self, page: Page):
        """После смены фильтра можно вернуться к 'Все врачи'"""
        dropdown = page.locator("#filter-doctor")
        dropdown.click()
        page.wait_for_timeout(600)
        options = page.locator("[class*='option']")
        if options.count() >= 2:
            options.nth(1).click()
            page.wait_for_timeout(2000)
        dropdown.click()
        page.wait_for_timeout(600)
        page.locator("text=Все врачи").first.click()
        page.wait_for_timeout(2500)
        assert not has_dash_error(page), "После сброса фильтра появилась ошибка Dash"


# ════════════════════════════════════════════════════════════════════════════════
# 4. ТЕСТЫ ГРАФИКОВ
# ════════════════════════════════════════════════════════════════════════════════
class TestCharts:

    def test_revenue_chart_visible(self, page: Page):
        """График 'Доходы по месяцам' отображается"""
        expect(page.locator("#chart-revenue")).to_be_visible()

    def test_status_chart_visible(self, page: Page):
        """График 'Статусы приёмов' отображается"""
        expect(page.locator("#chart-status")).to_be_visible()

    def test_doctors_chart_visible(self, page: Page):
        """График 'Нагрузка по врачам' отображается"""
        expect(page.locator("#chart-doctors")).to_be_visible()

    def test_diagnoses_chart_visible(self, page: Page):
        """График 'Топ диагнозов' отображается"""
        expect(page.locator("#chart-diagnoses")).to_be_visible()

    def test_heatmap_visible(self, page: Page):
        """Тепловая карта отображается"""
        expect(page.locator("#chart-heatmap")).to_be_visible()

    def test_materials_chart_visible(self, page: Page):
        """График материалов отображается"""
        expect(page.locator("#chart-materials")).to_be_visible()

    def test_scatter_chart_visible(self, page: Page):
        """Scatter-диаграмма отображается"""
        expect(page.locator("#chart-scatter")).to_be_visible()

    def test_all_charts_have_svg(self, page: Page):
        """Все графики содержат SVG-элементы (Plotly отрисовался)"""
        for chart_id in ["chart-revenue", "chart-status", "chart-doctors",
                         "chart-diagnoses", "chart-heatmap", "chart-materials", "chart-scatter"]:
            expect(page.locator(f"#{chart_id} svg").first).to_be_visible()

    def test_chart_hover_no_crash(self, page: Page):
        """Hover над графиком не вызывает Dash-ошибку"""
        # FIX: было locator("text=Error") — ложная тревога из-за DevTools
        page.locator("#chart-revenue .js-plotly-plot").hover()
        page.wait_for_timeout(800)
        assert not has_dash_error(page), "Hover вызвал ошибку Dash"

    def test_charts_have_plotly_class(self, page: Page):
        """Plotly отрисовал все графики (≥7 элементов с .js-plotly-plot)"""
        count = page.locator(".js-plotly-plot").count()
        assert count >= 7, f"Ожидалось ≥7 Plotly-графиков, найдено: {count}"


# ════════════════════════════════════════════════════════════════════════════════
# 5. ТЕСТЫ ТАБЛИЦЫ
# ════════════════════════════════════════════════════════════════════════════════
class TestDataTable:

    def test_table_visible(self, page: Page):
        """Таблица приёмов отображается"""
        expect(page.locator("#table-appointments")).to_be_visible()

    def test_table_has_rows(self, page: Page):
        """Таблица содержит строки данных"""
        rows = page.locator("#table-appointments tbody tr")
        assert rows.count() > 0, "Таблица пуста"

    def test_table_headers_present(self, page: Page):
        """Все заголовки таблицы присутствуют"""
        for header_text in ["Дата", "Врач", "Диагноз", "Статус", "Стоимость"]:
            expect(page.locator("#table-appointments th", has_text=header_text).first).to_be_visible()

    def test_table_pagination_exists(self, page: Page):
        """Пагинация таблицы отображается"""
        pagination = page.locator(".previous-next-container, .page-number")
        expect(pagination.first).to_be_visible()

    def test_table_sort_no_crash(self, page: Page):
        """Сортировка по столбцу не вызывает Dash-ошибку"""
        # FIX: было locator("text=Error") — ложная тревога
        page.locator("#table-appointments th", has_text="Стоимость").first.click()
        page.wait_for_timeout(800)
        assert not has_dash_error(page), "Сортировка вызвала ошибку Dash"


# ════════════════════════════════════════════════════════════════════════════════
# 6. ТЕСТЫ LAYOUT
# ════════════════════════════════════════════════════════════════════════════════
class TestLayout:

    def test_footer_visible(self, page: Page):
        """Футер приложения отображается"""
        expect(page.locator("text=Python + Plotly Dash")).to_be_visible()

    def test_heading_dokhody(self, page: Page):
        """Заголовок 'Доходы по месяцам' виден"""
        expect(page.locator("text=Доходы по месяцам")).to_be_visible()

    def test_heading_nagruzka(self, page: Page):
        """Заголовок 'Нагрузка по врачам' виден"""
        expect(page.locator("text=Нагрузка по врачам")).to_be_visible()

    def test_page_scroll_no_crash(self, page: Page):
        """Прокрутка страницы до конца не вызывает Dash-ошибку"""
        # FIX: было locator("text=Error") — ложная тревога
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        assert not has_dash_error(page), "Прокрутка вызвала ошибку Dash"

    def test_mobile_viewport_no_crash(self, page: Page):
        """Страница не падает на мобильном viewport (375x812)"""
        # FIX: было locator("text=Error") — ложная тревога
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(BASE_URL)
        page.wait_for_timeout(2500)
        assert not has_dash_error(page), "На мобильном viewport появилась ошибка Dash"

    def test_filter_labels_visible(self, page: Page):
        """Метки фильтров отображаются"""
        expect(page.locator("text=Врач:")).to_be_visible()
        expect(page.locator("text=Диагноз:")).to_be_visible()
        expect(page.locator("text=Период:")).to_be_visible()
