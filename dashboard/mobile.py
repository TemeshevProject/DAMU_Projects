"""Мобильная адаптация дашборда (CSS + Plotly)."""

from __future__ import annotations

import streamlit as st


def inject_mobile_styles() -> None:
    st.markdown(
        """
        <style>
        /* Колонки в один столбец на телефоне */
        @media (max-width: 768px) {
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }

            .block-container {
                padding-left: 0.65rem !important;
                padding-right: 0.65rem !important;
                max-width: 100% !important;
            }

            h1 {
                font-size: 1.35rem !important;
                line-height: 1.3 !important;
            }

            [data-testid="stMetric"] {
                background: #f4f6f8;
                border-radius: 10px;
                padding: 0.45rem 0.55rem;
            }

            [data-testid="stMetricLabel"] {
                font-size: 0.72rem !important;
            }

            [data-testid="stMetricValue"] {
                font-size: 1.05rem !important;
                line-height: 1.2 !important;
            }

            [data-testid="stPlotlyChart"] {
                min-height: 280px;
            }

            [data-testid="stDataFrame"] div {
                font-size: 0.78rem;
            }
        }

        /* Горизонтальная прокрутка таблицы на узких экранах */
        [data-testid="stDataFrame"] > div {
            overflow-x: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def plotly_mobile_config() -> dict:
    return {
        "displayModeBar": False,
        "responsive": True,
        "scrollZoom": False,
    }


def chart_layout_kwargs(height: int = 380) -> dict:
    return {
        "height": height,
        "margin": dict(l=8, r=8, t=36, b=8),
        "autosize": True,
        "legend": dict(orientation="h", yanchor="bottom", y=-0.25, x=0),
    }
