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

# 3. 상단 핵심 지표 (KPI)
st.subheader("📌 핵심 성과 지표")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("1분기 총 실매출액", f"{df['실매출액'].sum():,}원")
with m2:
    st.metric("1분기 총 인센티브", f"{df['인센티브'].sum():,}원")
with m3:
    st.metric("인센티브 대상자", f"{df['성명'].nunique()}명")

st.divider()

# 4. 개인별 인센티브 분석 (새로 추가된 섹션)
st.subheader("👤 개인별 누적 성과")
person_df = df.groupby("성명")[["실매출액", "인센티브"]].sum().sort_values(by="인센티브", ascending=False).reset_index()

# 개인별 지표 카드 표시
cols = st.columns(len(person_df))
for i, row in person_df.iterrows():
    with cols[i]:
        st.write(f"**{row['성명']}**")
        st.write(f"{row['인센티브']:,}원")

st.write("") # 간격 조절

# 5. 시각화 차트
c1, c2 = st.columns(2)

with c1:
    st.subheader("📅 월별 인센티브 추이")
    monthly_inc = df.groupby("월")["인센티브"].sum().reset_index()
    fig1 = px.bar(monthly_inc, x="월", y="인센티브", text_auto=',.0f', color_discrete_sequence=['#1f77b4'])
    fig1.update_layout(width=520, height=380)
    st.plotly_chart(fig1, use_container_width=False)

with c2:
    st.subheader("📊 개인별 누적 인센티브 합계")
    fig2 = px.bar(person_df, x="성명", y="인센티브", text_auto=',.0f', color="성명")
    st.plotly_chart(fig2, use_container_width=True)

# 6. 상세 데이터 테이블
st.subheader("🔍 상세 내역")
st.dataframe(df.style.format({"실매출액": "{:,}", "인센티브": "{:,}"}), use_container_width=True)