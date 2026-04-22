import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 페이지 설정
st.set_page_config(page_title="온리프 해외 매출 통합 관리", layout="wide")

# ✅ 사이드바 UI 개선
st.sidebar.title("🏨 온리프 해외 매출 대시보드")
menu = st.sidebar.radio(
    "메뉴 이동",
    ["🌐 전체 매출", "💸 에이전트별 수수료"],
    format_func=lambda x: f"{x}"
)
st.sidebar.markdown("---")
st.sidebar.subheader("📅 조회 기간 설정")

# 예시 데이터 (실제 코드에서는 기존 데이터 로딩 로직 사용)
months = ["25년 10월", "25년 11월", "25년 12월", "26년 1월", "26년 2월", "26년 3월"]
sel_month = st.sidebar.selectbox("상세 조회 월 선택", months, index=len(months)-1)

# KPI 카드 레이아웃
st.title(f"{sel_month} 해외 매출 현황")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("총 매출액", "125억 원", "+8.5%")
with col2:
    st.metric("수수료 미지급 매출", "80억 원", "+10.2%")
with col3:
    st.metric("수수료 지급 매출", "45억 원", "-2.1%")
with col4:
    st.metric("💡 앤파 컨설팅수수료(20%)", "25억 원", "+5.0%")

st.markdown("<hr>", unsafe_allow_html=True)

# 📈 분석 리포트 메시지
st.subheader("💡 AI 자동 분석 리포트")
st.success("📈 전월 대비 총매출 **+8.5% 성장** (+9억 원)")
st.info("🔥 가장 눈에 띄는 성장 국가: **베트남** (+50%)")
st.error("📉 중국 시장은 -10.7% 감소")

st.markdown("<hr>", unsafe_allow_html=True)

# 📊 국가별 매출 차트
sales_data = pd.DataFrame({
    "국가": ["미국", "일본", "중국", "베트남", "인도네시아"],
    "매출액": [40, 30, 25, 15, 15],
    "증감률": [14.3, -6.2, -10.7, 50.0, 25.0]
})

fig_bar = px.bar(
    sales_data, x="국가", y="매출액", color="국가",
    text="증감률", title="국가별 매출 및 증감률"
)
fig_bar.update_traces(texttemplate="%{text}%", textposition="outside")
st.plotly_chart(fig_bar, use_container_width=True)

# 📊 온라인/오프라인 매출 비중
channel_data = pd.DataFrame({
    "채널": ["온라인", "오프라인"],
    "비중": [70, 30]
})
fig_pie = px.pie(
    channel_data, values="비중", names="채널",
    hole=0.4, color="채널", color_discrete_map={"온라인": "#4CAF50", "오프라인": "#FFC107"}
)
fig_pie.update_traces(textinfo="percent+label")
st.plotly_chart(fig_pie, use_container_width=True)

# 📑 주요 이슈 및 리스크
st.subheader("⚠️ 주요 이슈 및 리스크")
st.warning("💱 환율 변동: 원/달러 환율 5% 상승 → 수익성 악화")
st.warning("🚚 중국 물류 지연: 평균 배송 지연 3일 → 고객 불만 증가")
st.warning("📜 일본 규제 강화: 인증 지연 → 출시 일정 차질")

# 📑 개선 과제 및 전략
st.subheader("🚀 개선 과제 및 전략")
st.markdown("""
- **Q2:** 동남아 신규 시장 진출 (말레이시아, 태국)
- **Q3:** 디지털 마케팅 강화 (SNS 캠페인 확대)
- **Q4:** 물류 파트너 다변화 및 재고 관리 최적화
""")

# 📑 결론 및 향후 계획
st.subheader("🎯 결론 및 향후 계획")
st.markdown("""
- **4월 목표 매출:** 140억 원  
- **중점 관리 국가:** 미국 🇺🇸, 베트남 🇻🇳, 인도네시아 🇮🇩  
- **리스크 대응 전략:** 환율 헤지, 물류 계약 재조정
""")
