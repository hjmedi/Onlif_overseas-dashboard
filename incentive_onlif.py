import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="온리프 인센티브 대시보드", layout="wide")

st.title("💰 해외사업본부 1분기 인센티브 리포트")
st.info("1월 ~ 3월 귀속분 통합 실적 및 개인별 성과 지표입니다.")

# 2. 데이터 정리
data = [
    {"월": "1월", "성명": "왕세신", "권역": "총괄", "실매출액": 130597270, "인센티브": 1958960},
    {"월": "1월", "성명": "채령", "권역": "중화권", "실매출액": 79944623, "인센티브": 399730},
    {"월": "1월", "성명": "단비", "권역": "영미권", "실매출액": 13912755, "인센티브": 69570},
    {"월": "1월", "성명": "장원희", "권역": "일본", "실매출액": 13137000, "인센티브": 131370},
    {"월": "2월", "성명": "왕세신", "권역": "총괄", "실매출액": 84637449, "인센티브": 1269570},
    {"월": "2월", "성명": "채령", "권역": "중화권", "실매출액": 66877831, "인센티브": 668780},
    {"월": "2월", "성명": "단비", "권역": "영미권", "실매출액": 12383059, "인센티브": 61920},
    {"월": "2월", "성명": "장원희", "권역": "일본", "실매출액": 9493900, "인센티브": 94940},
    {"월": "3월", "성명": "왕세신", "권역": "총괄", "실매출액": 121089732, "인센티브": 1816350},
    {"월": "3월", "성명": "김홍실", "권역": "중화권", "실매출액": 33134045, "인센티브": 275850},
    {"월": "3월", "성명": "단비", "권역": "영미권", "실매출액": 50183723, "인센티브": 250920},
    {"월": "3월", "성명": "장원희", "권역": "일본", "실매출액": 95387311, "인센티브": 953880},
]

df = pd.DataFrame(data)
month_order = ["1월", "2월", "3월"]
available_months = [m for m in month_order if m in df["월"].unique()]

selected_months = st.multiselect(
    "조회할 월 선택",
    options=available_months,
    default=available_months,
)

if not selected_months:
    st.warning("최소 1개 이상의 월을 선택해주세요.")
    st.stop()

df_filtered = df[df["월"].isin(selected_months)].copy()
latest_month = max(selected_months, key=lambda m: month_order.index(m))
df_current = df[df["월"] == latest_month].copy()

# 3. 상단 핵심 지표 (KPI)
st.subheader("📌 핵심 성과 지표")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("선택 기간 총 실매출액", f"{df_filtered['실매출액'].sum():,}원")
with m2:
    st.metric("선택 기간 총 인센티브", f"{df_filtered['인센티브'].sum():,}원")
with m3:
    st.metric("인센티브 대상자", f"{df_filtered['성명'].nunique()}명")

st.divider()

# 4. 개인별 인센티브 분석 (새로 추가된 섹션)
st.subheader("👤 개인별 누적 성과")
person_df = (
    df_filtered.groupby("성명")[["실매출액", "인센티브"]]
    .sum()
    .sort_values(by="인센티브", ascending=False)
    .reset_index()
)
name_order = person_df["성명"].tolist()
palette = px.colors.qualitative.Plotly
color_map = {name: palette[i % len(palette)] for i, name in enumerate(name_order)}

# 개인별 지표 카드 표시
cols = st.columns(len(person_df))
for i, row in person_df.iterrows():
    with cols[i]:
        st.write(f"**{row['성명']}**")
        st.write(f"{row['인센티브']:,}원")

st.write("")  # 간격 조절

# 5. 시각화 차트 (당월)
c1, c2 = st.columns(2)

with c1:
    st.subheader(f"📅 당월 인센티브 구성 ({latest_month})")
    current_stack = (
        df_current.groupby(["월", "성명"], as_index=False)["인센티브"]
        .sum()
    )
    fig1 = px.bar(
        current_stack,
        x="월",
        y="인센티브",
        color="성명",
        category_orders={"성명": name_order},
        color_discrete_map=color_map,
    )
    current_total_incentive = float(df_current["인센티브"].sum())
    fig1.update_layout(height=380, bargap=0.45, barmode="stack")
    fig1.update_yaxes(range=[0, current_total_incentive * 1.1 if current_total_incentive else 1])
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.subheader(f"📊 당월 개인별 인센티브 ({latest_month})")
    current_person_df = (
        df_current.groupby("성명", as_index=False)["인센티브"]
        .sum()
        .sort_values(by="인센티브", ascending=False)
    )
    fig2 = px.bar(
        current_person_df,
        x="성명",
        y="인센티브",
        text_auto=',.0f',
        color="성명",
        category_orders={"성명": name_order},
        color_discrete_map=color_map,
    )
    fig2.update_layout(height=380)
    fig2.update_yaxes(range=[0, current_total_incentive * 1.1 if current_total_incentive else 1])
    st.plotly_chart(fig2, use_container_width=True)

# 6. 누적 시각화 (선택 기간)
st.subheader("📈 누적 개인별 인센티브 합계 (선택 기간)")
fig3 = px.bar(
    person_df,
    x="성명",
    y="인센티브",
    text_auto=',.0f',
    color="성명",
    category_orders={"성명": name_order},
    color_discrete_map=color_map,
)
fig3.update_layout(height=360)
st.plotly_chart(fig3, use_container_width=True)

# 7. 상세 데이터 테이블
st.subheader("🔍 상세 내역")
st.dataframe(
    df_filtered.style.format({"실매출액": "{:,}", "인센티브": "{:,}"}),
    use_container_width=True,
)