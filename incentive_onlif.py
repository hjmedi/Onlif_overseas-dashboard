import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(page_title="직원 인센티브 대시보드", layout="wide")

st.title("직원 인센티브 산정 및 실적 분석")
st.caption("인센티브 3종별 규칙을 각각 설정하고, 월별 실적/지급 추이를 비교합니다.")


def pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def normalize_input(df: pd.DataFrame) -> pd.DataFrame:
    date_col = pick_col(df, ["date", "날짜", "매출일", "수납일"])
    emp_col = pick_col(df, ["employee", "직원", "담당자", "사원명", "이름"])
    sales_col = pick_col(df, ["sales", "매출", "매출액", "수납액"])

    if not date_col or not emp_col or not sales_col:
        raise ValueError(
            "필수 컬럼을 찾지 못했습니다. 날짜/직원/매출 컬럼이 필요합니다. "
            "(예: 날짜, 직원, 매출액)"
        )

    out = df[[date_col, emp_col, sales_col]].copy()
    out.columns = ["date", "employee", "sales"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["sales"] = (
        out["sales"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("원", "", regex=False)
        .str.strip()
    )
    out["sales"] = pd.to_numeric(out["sales"], errors="coerce")
    out = out.dropna(subset=["date", "employee", "sales"])
    out["month"] = out["date"].dt.to_period("M").astype(str)
    return out


def incentive_from_sales(
    sales: float,
    tier1_cap: float,
    tier2_cap: float,
    tier1_rate: float,
    tier2_rate: float,
    tier3_rate: float,
) -> float:
    if sales <= tier1_cap:
        return sales * tier1_rate
    if sales <= tier2_cap:
        return sales * tier2_rate
    return sales * tier3_rate


def render_incentive_tab(
    tab_label: str,
    base_data: pd.DataFrame,
    key_prefix: str,
    default_tier1_cap: int,
    default_tier2_cap: int,
    default_tier1_rate: float,
    default_tier2_rate: float,
    default_tier3_rate: float,
) -> None:
    st.markdown(f"### {tab_label} 규칙")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        tier1_cap = st.number_input(
            "1구간 상한(원)",
            value=default_tier1_cap,
            step=100_000,
            key=f"{key_prefix}_tier1_cap",
        )
    with c2:
        tier2_cap = st.number_input(
            "2구간 상한(원)",
            value=default_tier2_cap,
            step=100_000,
            key=f"{key_prefix}_tier2_cap",
        )
    with c3:
        tier1_rate = (
            st.slider(
                "1구간 인센티브율(%)",
                0.0,
                30.0,
                default_tier1_rate,
                0.5,
                key=f"{key_prefix}_tier1_rate",
            )
            / 100
        )
    with c4:
        tier2_rate = (
            st.slider(
                "2구간 인센티브율(%)",
                0.0,
                30.0,
                default_tier2_rate,
                0.5,
                key=f"{key_prefix}_tier2_rate",
            )
            / 100
        )
    with c5:
        tier3_rate = (
            st.slider(
                "3구간 인센티브율(%)",
                0.0,
                30.0,
                default_tier3_rate,
                0.5,
                key=f"{key_prefix}_tier3_rate",
            )
            / 100
        )

    monthly = (
        base_data.groupby(["month", "employee"], as_index=False)["sales"]
        .sum()
        .sort_values(["month", "employee"])
    )
    monthly["incentive"] = monthly["sales"].apply(
        lambda sales: incentive_from_sales(
            sales, tier1_cap, tier2_cap, tier1_rate, tier2_rate, tier3_rate
        )
    )

    total_sales = monthly["sales"].sum()
    total_incentive = monthly["incentive"].sum()
    employee_count = monthly["employee"].nunique()

    m1, m2, m3 = st.columns(3)
    m1.metric("총 매출", f"{total_sales:,.0f}원")
    m2.metric("총 인센티브", f"{total_incentive:,.0f}원")
    m3.metric("직원 수", f"{employee_count}명")

    st.markdown("---")
    st.subheader("월별 실적 및 인센티브 추이")
    month_summary = monthly.groupby("month", as_index=False)[["sales", "incentive"]].sum()
    fig_trend = px.line(
        month_summary,
        x="month",
        y=["sales", "incentive"],
        markers=True,
        labels={"value": "금액", "month": "월", "variable": "지표"},
    )
    fig_trend.update_layout(yaxis_tickformat=",")
    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader("직원별 월 인센티브")
    fig_emp_inc = px.bar(
        monthly,
        x="month",
        y="incentive",
        color="employee",
        barmode="group",
        labels={"incentive": "인센티브", "month": "월", "employee": "직원"},
    )
    fig_emp_inc.update_layout(yaxis_tickformat=",")
    st.plotly_chart(fig_emp_inc, use_container_width=True)

    st.subheader("인센티브 산정 결과")
    show_cols = monthly.rename(
        columns={"month": "월", "employee": "직원", "sales": "매출", "incentive": "인센티브"}
    )
    st.dataframe(show_cols, use_container_width=True)

    csv_out = show_cols.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        f"{tab_label} 결과 CSV 다운로드",
        data=csv_out,
        file_name=f"{key_prefix}_result.csv",
        mime="text/csv",
        key=f"{key_prefix}_download",
    )


uploaded = st.file_uploader("실적 파일 업로드 (CSV)", type=["csv"])

if uploaded is None:
    st.info("CSV를 업로드하면 직원별 인센티브와 추이 그래프가 표시됩니다.")
    st.markdown(
        "- 필수 컬럼 예시: `날짜`, `직원`, `매출액`\n"
        "- 컬럼명 영문도 가능: `date`, `employee`, `sales`"
    )
    st.stop()

try:
    raw_df = pd.read_csv(uploaded)
    data = normalize_input(raw_df)
except Exception as e:
    st.error(f"데이터 처리 중 오류: {e}")
    st.stop()

if data.empty:
    st.warning("유효한 데이터가 없습니다. 날짜/직원/매출 값을 확인해주세요.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["온리프 인센티브", "인센티브 유형 2", "인센티브 유형 3"])

with tab1:
    render_incentive_tab(
        tab_label="온리프 인센티브",
        base_data=data,
        key_prefix="onlif",
        default_tier1_cap=5_000_000,
        default_tier2_cap=10_000_000,
        default_tier1_rate=3.0,
        default_tier2_rate=5.0,
        default_tier3_rate=7.0,
    )

with tab2:
    render_incentive_tab(
        tab_label="인센티브 유형 2",
        base_data=data,
        key_prefix="type2",
        default_tier1_cap=4_000_000,
        default_tier2_cap=8_000_000,
        default_tier1_rate=2.0,
        default_tier2_rate=4.0,
        default_tier3_rate=6.0,
    )

with tab3:
    render_incentive_tab(
        tab_label="인센티브 유형 3",
        base_data=data,
        key_prefix="type3",
        default_tier1_cap=6_000_000,
        default_tier2_cap=12_000_000,
        default_tier1_rate=2.5,
        default_tier2_rate=4.5,
        default_tier3_rate=6.5,
    )

