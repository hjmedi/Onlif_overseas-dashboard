import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="온리프 인센티브 대시보드", layout="wide")

st.title("💰 해외사업본부 1분기 인센티브 리포트")
st.info("1월 ~ 3월 귀속분 통합 실적 및 개인별 성과 지표입니다.")

# 2. 데이터 정리 (기안서 기반)
data = [
    # 1월 [cite: 10, 31]
    {"월": "1월", "성명": "왕세신", "권역": "총괄", "실매출액": 130597270, "인센티브": 1958960},
    {"월": "1월", "성명": "채령", "권역": "중화권", "실매출액": 79944623, "인센티브": 399730},
    {"월": "1월", "성명": "단비", "권역": "영미권", "실매출액": 13912755, "인센티브": 69570},
    {"월": "1월", "성명": "장원희", "권역": "일본", "실매출액": 13137000, "인센티브": 131370},
    # 2월 [cite: 41, 64]
    {"월": "2월", "성명": "왕세신", "권역": "총괄", "실매출액": 84637449, "인센티브": 1269570},
    {"월": "2월", "성명": "채령", "권역": "중화권", "실매출액": 66877831, "인센티브": 668780},
    {"월": "2월", "성명": "단비", "권역": "영미권", "실매출액": 12383059, "인센티브": 61920},
    {"월": "2월", "성명": "장원희", "권역": "일본", "실매출액": 9493900, "인센티브": 94940},
    # 3월 [cite: 77, 97]
    {"월": "3월", "성명": "왕세신", "권역": "총괄", "실매출액": 121089732, "인센티브": 1816350},
    {"월": "3월", "성명": "김홍실", "권역": "중화권", "실매출액": 33134045, "인센티브": 275850},
    {"월": "3월", "성명": "단비", "권역": "영미권", "실매출액": 50183723, "인센티브": 250920},
    {"월": "3월", "성명": "장원희", "권역": "일본", "실매출액": 95387311, "인센티브": 953880},
]

df = pd.DataFrame(data)

# 3. 상단 핵심 지표
st.subheader("📌 1분기 누적 성과")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("총 실매출액", f"{df['실매출액'].sum():,}원") [cite: 10, 41, 77]
with m2:
    st.metric("총 인센티브", f"{df['인센티브'].sum():,}원") [cite: 10, 41, 77]
with m3:
    st.metric("평균 인센티브율", f"{(df['인센티브'].sum() / df['실매출액'].sum() * 100):.2f}%")

st.divider()

# 4. 개인별 인센티브 요약 (요청하신 부분)
st.subheader("👤 개인별 누적 인센티브 현황")
person_summary = df.groupby("성명")["인센티브"].sum().sort_values(ascending=False).reset_index()

# 깔끔한 카드 형태로 표시
cols = st.columns(len(person_summary))
for i, row in person_summary.iterrows():
    with cols[i]:
        st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background-color:#f0f2f6; text-align:center;">
            <p style="margin:0; color:#555;">{row['성명']}</p>
            <h3 style="margin:0; color:#1f77b4;">{row['인센티브']:,}원</h3>
        </div>
        """, unsafe_allow_html=True)

st.write("") # 간격

# 5. 차트 분석
c1, c2 = st.columns(2)
with c1:
    st.subheader("📅 월별 실적 추이")
    monthly = df.groupby("월")["인센티브"].sum().reset_index()
    st.plotly_chart(px.line(monthly, x="월", y="인센티브", markers=True), use_container_width=True)
with c2:
    st.subheader("📊 성명별 인센티브 합계")
    st.plotly_chart(px.bar(person_summary, x="성명", y="인센티브", color="성명", text_auto=',.0f'), use_container_width=True)

# 6. 상세 테이블
st.subheader("🔍 상세 지급 내역")
st.dataframe(df.style.format({"실매출액": "{:,}", "인센티브": "{:,}"}), use_container_width=True)