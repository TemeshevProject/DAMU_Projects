"""Интерактивный дашборд проектов ДАМУ."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.data import COLUMN_LABELS, DISPLAY_COLUMNS, format_amount, load_projects

st.set_page_config(
    page_title="ДАМУ — проекты",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

SUPPORT_LABELS = {
    "subsidization": "Субсидирование",
    "guarantee": "Гарантирование",
}


@st.cache_data(show_spinner="Загрузка данных...")
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


def sidebar_filters(df: pd.DataFrame) -> None:
    st.sidebar.header("Фильтры")

    st.session_state["search"] = st.sidebar.text_input(
        "Поиск (компания / проект)",
        value=st.session_state.get("search", ""),
    )

    regions = sorted(df["region"].dropna().unique().tolist())
    st.session_state["regions"] = st.sidebar.multiselect("Регион", regions)

    support_types = sorted(df["support_type"].dropna().unique().tolist())
    st.session_state["support_types"] = st.sidebar.multiselect(
        "Тип поддержки",
        support_types,
        format_func=lambda x: SUPPORT_LABELS.get(x, x),
    )

    programs = sorted(df["program"].dropna().unique().tolist())
    st.session_state["programs"] = st.sidebar.multiselect("Программа", programs)

    banks = sorted(df["bank"].dropna().unique().tolist())
    st.session_state["banks"] = st.sidebar.multiselect("Банк", banks)

    legal_forms = sorted(df["legal_form"].dropna().unique().tolist())
    st.session_state["legal_forms"] = st.sidebar.multiselect("ОПФ", legal_forms)

    st.session_state["oked_prefix"] = st.sidebar.text_input(
        "Код ОКЭД (префикс)",
        value=st.session_state.get("oked_prefix", ""),
        help="Например: 47 — розничная торговля",
    )

    years = sorted([int(y) for y in df["year"].dropna().unique().tolist()])
    st.session_state["years"] = st.sidebar.multiselect("Год", years)

    max_credit = float(df["credit_amount"].fillna(0).max() or 0)
    amount_range = st.sidebar.slider(
        "Сумма кредита, ₸",
        min_value=0,
        max_value=int(max_credit) if max_credit > 0 else 1,
        value=(
            st.session_state.get("min_amount", 0),
            st.session_state.get("max_amount", int(max_credit) if max_credit > 0 else 1),
        ),
        step=1_000_000,
    )
    st.session_state["min_amount"] = amount_range[0]
    st.session_state["max_amount"] = amount_range[1]

    if st.sidebar.button("Сбросить фильтры"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def show_metrics(df: pd.DataFrame) -> None:
    total_credit = df["credit_amount"].fillna(0).sum()
    total_guarantee = df["guarantee_amount"].fillna(0).sum()
    companies = df["company_name"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Проектов", f"{len(df):,}".replace(",", " "))
    c2.metric("Уникальных компаний", f"{companies:,}".replace(",", " "))
    c3.metric("Сумма кредитов", format_amount(total_credit) + " ₸")
    c4.metric("Сумма гарантий", format_amount(total_guarantee) + " ₸")


def show_charts(df: pd.DataFrame) -> None:
    chart_df = df.copy()
    chart_df["credit_amount"] = chart_df["credit_amount"].fillna(0)

    left, right = st.columns(2)

    with left:
        by_region = (
            chart_df.groupby("region", as_index=False)["credit_amount"]
            .sum()
            .sort_values("credit_amount", ascending=False)
            .head(15)
        )
        fig = px.bar(
            by_region,
            x="credit_amount",
            y="region",
            orientation="h",
            title="Топ-15 регионов по сумме кредитов",
            labels={"credit_amount": "Сумма, ₸", "region": "Регион"},
        )
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with right:
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
            title="Структура по типу поддержки (кол-во)",
            hole=0.35,
        )
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    left2, right2 = st.columns(2)

    with left2:
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
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with right2:
        by_oked = (
            chart_df.groupby("oked_code", as_index=False)["credit_amount"]
            .sum()
            .sort_values("credit_amount", ascending=False)
            .head(12)
        )
        fig = px.bar(
            by_oked,
            x="oked_code",
            y="credit_amount",
            title="Топ-12 кодов ОКЭД по сумме кредитов",
            labels={"credit_amount": "Сумма, ₸", "oked_code": "ОКЭД"},
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)


def show_table(df: pd.DataFrame) -> None:
    st.subheader("Детальная таблица")

    cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
    view = df[cols].copy()
    view = view.rename(columns={c: COLUMN_LABELS.get(c, c) for c in cols})

    st.caption(f"Показано {len(view):,} записей. Таблица поддерживает сортировку и прокрутку.".replace(",", " "))

    st.dataframe(
        view,
        use_container_width=True,
        height=520,
        column_config={
            COLUMN_LABELS["credit_amount"]: st.column_config.NumberColumn(format="%,.0f"),
            COLUMN_LABELS["guarantee_amount"]: st.column_config.NumberColumn(format="%,.0f"),
        },
    )

    csv_bytes = view.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "Скачать отфильтрованные данные (CSV)",
        data=csv_bytes,
        file_name="damu_filtered.csv",
        mime="text/csv",
    )


def main() -> None:
    st.title("ДАМУ — проекты с государственной поддержкой")
    st.markdown(
        "Интерактивный дашборд по открытым отчётам "
        "[damu.kz/ru/reports/](https://damu.kz/ru/reports/). "
        "Данные: субсидирование и гарантирование."
    )

    try:
        df = get_data()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    sidebar_filters(df)
    filtered = apply_filters(df)

    show_metrics(filtered)
    show_charts(filtered)
    show_table(filtered)


if __name__ == "__main__":
    main()
