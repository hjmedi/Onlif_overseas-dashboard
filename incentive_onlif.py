import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(page_title="직원 인센티브 대시보드", layout="wide")

st.title("직원 인센티브 산정 및 실적 분석")
st.caption("월 매출 기반으로 직원별 인센티브를 자동 계산하고 추이를 확인합니다.")


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


with st.sidebar:
    st.header("인센티브 규칙")
    tier1_cap = st.number_input("1구간 상한 (원)", value=5_000_000, step=100_000)
    tier2_cap = st.number_input("2구간 상한 (원)", value=10_000_000, step=100_000)
    tier1_rate = st.slider("1구간 인센티브율 (%)", 0.0, 20.0, 3.0, 0.5) / 100
    tier2_rate = st.slider("2구간 인센티브율 (%)", 0.0, 20.0, 5.0, 0.5) / 100
    tier3_rate = st.slider("3구간 인센티브율 (%)", 0.0, 20.0, 7.0, 0.5) / 100


def incentive_from_sales(sales: float) -> float:
    if sales <= tier1_cap:
        return sales * tier1_rate
    if sales <= tier2_cap:
        return sales * tier2_rate
    return sales * tier3_rate


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

monthly = (
    data.groupby(["month", "employee"], as_index=False)["sales"]
    .sum()
    .sort_values(["month", "employee"])
)
monthly["incentive"] = monthly["sales"].apply(incentive_from_sales)

total_sales = monthly["sales"].sum()
total_incentive = monthly["incentive"].sum()
employee_count = monthly["employee"].nunique()

c1, c2, c3 = st.columns(3)
c1.metric("총 매출", f"{total_sales:,.0f}원")
c2.metric("총 인센티브", f"{total_incentive:,.0f}원")
c3.metric("직원 수", f"{employee_count}명")

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

st.subheader("직원별 월 매출")
fig_emp_sales = px.bar(
    monthly,
    x="month",
    y="sales",
    color="employee",
    barmode="group",
    labels={"sales": "매출", "month": "월", "employee": "직원"},
)
fig_emp_sales.update_layout(yaxis_tickformat=",")
st.plotly_chart(fig_emp_sales, use_container_width=True)

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
    "인센티브 결과 CSV 다운로드",
    data=csv_out,
    file_name="incentive_result.csv",
    mime="text/csv",
)

