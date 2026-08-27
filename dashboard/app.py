"""Интерактивный дашборд проектов ДАМУ."""

from __future__ import annotations

import re

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.data import (
    COLUMN_LABELS,
    DISPLAY_COLUMNS,
    MOBILE_DISPLAY_COLUMNS,
    format_amount_compact,
    load_projects,
)
from dashboard.mobile import chart_layout_kwargs, inject_mobile_styles, plotly_mobile_config

st.set_page_config(
    page_title="ДАМУ — проекты",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_mobile_styles()

SUPPORT_LABELS = {
    "subsidization": "Субсидирование",
    "guarantee": "Гарантирование",
}

PLOTLY_CONFIG = plotly_mobile_config()


@st.cache_data(show_spinner="Загрузка данных ДАМУ (при первом запуске может занять 1–2 минуты)...")
def get_data() -> pd.DataFrame:
    return load_projects()


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()

    if st.session_state.get("search"):
        term = st.session_state["search"].strip()
        mask = (
            filtered["company_name"].fillna("").str.contains(term, case=False, na=False)
            | filtered["project_name"].fillna("").str.contains(term, case=False, na=False)
        )
        filtered = filtered[mask]

    if st.session_state.get("bin_filter"):
        term = st.session_state["bin_filter"].strip()
        mask = filtered["bin"].fillna("").str.contains(term, na=False)
        filtered = filtered[mask]

    if st.session_state.get("iin_filter"):
        term = st.session_state["iin_filter"].strip()
        mask = filtered["iin"].fillna("").str.contains(term, na=False)
        filtered = filtered[mask]

    if st.session_state.get("id_filter"):
        term = re.sub(r"\D", "", st.session_state["id_filter"])
        if term:
            mask = (
                filtered["bin"].fillna("").str.contains(term, na=False)
                | filtered["iin"].fillna("").str.contains(term, na=False)
            )
            filtered = filtered[mask]

    if st.session_state.get("regions"):
        filtered = filtered[filtered["region"].isin(st.session_state["regions"])]

    if st.session_state.get("support_types"):
        filtered = filtered[filtered["support_type"].isin(st.session_state["support_types"])]

    if st.session_state.get("programs"):
        filtered = filtered[filtered["program"].isin(st.session_state["programs"])]

    if st.session_state.get("banks"):
        filtered = filtered[filtered["bank"].isin(st.session_state["banks"])]

    if st.session_state.get("legal_forms"):
        filtered = filtered[filtered["legal_form"].isin(st.session_state["legal_forms"])]

    if st.session_state.get("oked_prefix"):
        prefix = st.session_state["oked_prefix"].strip()
        filtered = filtered[filtered["oked_code"].fillna("").str.startswith(prefix)]

    if st.session_state.get("years"):
        filtered = filtered[filtered["year"].isin(st.session_state["years"])]

    min_amount = st.session_state.get("min_amount", 0)
    max_amount = st.session_state.get("max_amount", float("inf"))
    amount_col = filtered["credit_amount"].fillna(0)
    filtered = filtered[(amount_col >= min_amount) & (amount_col <= max_amount)]

    return filtered


def quick_filters_hint() -> None:
    """Подсказка для мобильных — фильтры только в боковой панели."""
    with st.expander("🔍 Как фильтровать на телефоне", expanded=False):
        st.markdown(
            "1. Нажмите **☰** вверху слева\n"
            "2. Выберите регион, ОКЭД, банк и другие фильтры\n"
            "3. Закройте панель — дашборд обновится автоматически"
        )


def sidebar_filters(df: pd.DataFrame) -> None:
    st.sidebar.header("Фильтры")
    st.sidebar.caption("На телефоне: откройте панель через ☰ вверху.")

    if "search" not in st.session_state:
        st.session_state["search"] = ""
    st.sidebar.text_input(
        "Поиск (компания / проект)",
        key="search",
        placeholder="Например: макарон, ForteBank…",
    )

    st.sidebar.text_input(
        "БИН",
        key="bin_filter",
        placeholder="12 цифр или часть",
    )

    st.sidebar.text_input(
        "ИИН",
        key="iin_filter",
        placeholder="12 цифр или часть",
    )

    st.sidebar.text_input(
        "БИН или ИИН",
        key="id_filter",
        placeholder="Любой идентификатор",
    )

    regions = sorted(df["region"].dropna().unique().tolist())
    if "regions" not in st.session_state:
        st.session_state["regions"] = []
    st.sidebar.multiselect("Регион", regions, key="regions")

    support_types = sorted(df["support_type"].dropna().unique().tolist())
    if "support_types" not in st.session_state:
        st.session_state["support_types"] = []
    st.sidebar.multiselect(
        "Тип поддержки",
        support_types,
        key="support_types",
        format_func=lambda x: SUPPORT_LABELS.get(x, x),
    )

    programs = sorted(df["program"].dropna().unique().tolist())
    if "programs" not in st.session_state:
        st.session_state["programs"] = []
    st.sidebar.multiselect("Программа", programs, key="programs")

    banks = sorted(df["bank"].dropna().unique().tolist())
    if "banks" not in st.session_state:
        st.session_state["banks"] = []
    st.sidebar.multiselect("Банк", banks, key="banks")

    legal_forms = sorted(df["legal_form"].dropna().unique().tolist())
    if "legal_forms" not in st.session_state:
        st.session_state["legal_forms"] = []
    st.sidebar.multiselect("ОПФ", legal_forms, key="legal_forms")

    if "oked_prefix" not in st.session_state:
        st.session_state["oked_prefix"] = ""
    st.sidebar.text_input(
        "Код ОКЭД (префикс)",
        key="oked_prefix",
        help="Например: 47 — розничная торговля",
    )

    years = sorted([int(y) for y in df["year"].dropna().unique().tolist()])
    if "years" not in st.session_state:
        st.session_state["years"] = []
    st.sidebar.multiselect("Год", years, key="years")

    max_credit = float(df["credit_amount"].fillna(0).max() or 0)
    default_max = int(max_credit) if max_credit > 0 else 1
    if "min_amount" not in st.session_state:
        st.session_state["min_amount"] = 0
    if "max_amount" not in st.session_state:
        st.session_state["max_amount"] = default_max

    amount_range = st.sidebar.slider(
        "Сумма кредита, ₸",
        min_value=0,
        max_value=default_max,
        value=(st.session_state["min_amount"], st.session_state["max_amount"]),
        step=1_000_000,
    )
    st.session_state["min_amount"] = amount_range[0]
    st.session_state["max_amount"] = amount_range[1]

    if st.sidebar.button("Сбросить фильтры", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def show_metrics(df: pd.DataFrame) -> None:
    total_credit = df["credit_amount"].fillna(0).sum()
    total_guarantee = df["guarantee_amount"].fillna(0).sum()
    companies = df["company_name"].nunique()

    credit_short, credit_full = format_amount_compact(total_credit)
    guarantee_short, guarantee_full = format_amount_compact(total_guarantee)

    r1_left, r1_right = st.columns(2)
    r1_left.metric("Проектов", f"{len(df):,}".replace(",", " "))
    r1_right.metric("Компаний", f"{companies:,}".replace(",", " "))

    r2_left, r2_right = st.columns(2)
    r2_left.metric("Сумма кредитов", credit_short, help=credit_full)
    r2_right.metric("Сумма гарантий", guarantee_short, help=guarantee_full)


def _plot_chart(fig) -> None:
    st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG)


def show_charts(df: pd.DataFrame) -> None:
    chart_df = df.copy()
    chart_df["credit_amount"] = chart_df["credit_amount"].fillna(0)

    by_region = (
        chart_df.groupby("region", as_index=False)["credit_amount"]
        .sum()
        .sort_values("credit_amount", ascending=False)
        .head(10)
    )
    fig = px.bar(
        by_region,
        x="credit_amount",
        y="region",
        orientation="h",
        title="Топ-10 регионов по сумме кредитов",
        labels={"credit_amount": "Сумма, ₸", "region": "Регион"},
    )
    fig.update_layout(**chart_layout_kwargs(340))
    _plot_chart(fig)

    left, right = st.columns(2)

    with left:
        by_support = (
            chart_df.groupby("support_type", as_index=False)
            .agg(count=("company_name", "count"), amount=("credit_amount", "sum"))
        )
        by_support["label"] = by_support["support_type"].map(
            lambda x: SUPPORT_LABELS.get(x, x)
        )
        fig = px.pie(
            by_support,
            names="label",
            values="count",
            title="Тип поддержки (кол-во)",
            hole=0.35,
        )
        fig.update_layout(**chart_layout_kwargs(320))
        _plot_chart(fig)

    with right:
        by_oked = (
            chart_df.groupby("oked_code", as_index=False)["credit_amount"]
            .sum()
            .sort_values("credit_amount", ascending=False)
            .head(8)
        )
        fig = px.bar(
            by_oked,
            x="oked_code",
            y="credit_amount",
            title="Топ-8 кодов ОКЭД",
            labels={"credit_amount": "Сумма, ₸", "oked_code": "ОКЭД"},
        )
        fig.update_layout(**chart_layout_kwargs(320))
        _plot_chart(fig)

    by_year = (
        chart_df.dropna(subset=["year"])
        .groupby("year", as_index=False)
        .agg(count=("company_name", "count"), amount=("credit_amount", "sum"))
    )
    if not by_year.empty:
        fig = px.line(
            by_year,
            x="year",
            y="amount",
            markers=True,
            title="Динамика суммы кредитов по годам",
            labels={"amount": "Сумма, ₸", "year": "Год"},
        )
        fig.update_layout(**chart_layout_kwargs(300))
        _plot_chart(fig)


def _prepare_table_view(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    cols = [c for c in columns if c in df.columns]
    view = df[cols].copy()
    return view.rename(columns={c: COLUMN_LABELS.get(c, c) for c in cols})


def show_table(df: pd.DataFrame) -> None:
    st.subheader("Детальная таблица")

    tab_short, tab_full = st.tabs(["Кратко (для телефона)", "Все поля"])

    with tab_short:
        view = _prepare_table_view(df, MOBILE_DISPLAY_COLUMNS)
        st.caption(f"{len(view):,} записей — свайп влево для прокрутки колонок".replace(",", " "))
        st.dataframe(
            view,
            width="stretch",
            height=380,
            column_config={
                COLUMN_LABELS["credit_amount"]: st.column_config.NumberColumn(format="%,.0f"),
            },
        )

    with tab_full:
        view = _prepare_table_view(df, DISPLAY_COLUMNS)
        st.caption(f"{len(view):,} записей".replace(",", " "))
        st.dataframe(
            view,
            width="stretch",
            height=420,
            column_config={
                COLUMN_LABELS["credit_amount"]: st.column_config.NumberColumn(format="%,.0f"),
                COLUMN_LABELS["guarantee_amount"]: st.column_config.NumberColumn(format="%,.0f"),
            },
        )

    csv_bytes = _prepare_table_view(df, DISPLAY_COLUMNS).to_csv(
        index=False, encoding="utf-8-sig"
    ).encode("utf-8-sig")
    st.download_button(
        "Скачать CSV",
        data=csv_bytes,
        file_name="damu_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )


def main() -> None:
    st.title("ДАМУ — проекты")
    st.caption(
        "Открытые отчёты [damu.kz](https://damu.kz/ru/reports/) · "
        "БИН — реестр ЮЛ [data.egov.kz](https://data.egov.kz/datasets/view?index=gbd_ul) · "
        "ИИН для ИП в открытых отчётах ДАМУ не публикуется"
    )

    try:
        df = get_data()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    quick_filters_hint()
    sidebar_filters(df)
    filtered = apply_filters(df)

    show_metrics(filtered)
    show_charts(filtered)
    show_table(filtered)


if __name__ == "__main__":
    main()
