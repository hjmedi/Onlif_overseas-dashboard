import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="온리프 인센티브 대시보드", layout="wide")

st.title("💰 해외사업본부 1분기 인센티브 리포트")
st.caption("1월 ~ 3월 귀속분 통합 실적")

# 1. 통합 데이터 (기안서 기반 정확한 수치)
data = [
    # 1월 실적
    {"월": "1월", "성명": "왕세신", "권역": "총괄", "실매출액": 130597270, "인센티브": 1958960},
    {"월": "1월", "성명": "채령", "권역": "중화권", "실매출액": 79944623, "인센티브": 399730},
    {"월": "1월", "성명": "단비", "권역": "영미권", "실매출액": 13912755, "인센티브": 69570},
    {"월": "1월", "성명": "장원희", "권역": "일본", "실매출액": 13137000, "인센티브": 131370},
    # 2월 실적
    {"월": "2월", "성명": "왕세신", "권역": "총괄", "실매출액": 84637449, "인센티브": 1269570},
    {"월": "2월", "성명": "채령", "권역": "중화권", "실매출액": 66877831, "인센티브": 668780},
    {"월": "2월", "성명": "단비", "권역": "영미권", "실매출액": 12383059, "인센티브": 61920},
    {"월": "2월", "성명": "장원희", "권역": "일본", "실매출액": 9493900, "인센티브": 94940},
    # 3월 실적
    {"월": "3월", "성명": "왕세신", "권역": "총괄", "실매출액": 121089732, "인센티브": 1816350},
    {"월": "3월", "성명": "김홍실", "권역": "중화권", "실매출액": 33134045, "인센티브": 275850},
    {"월": "3월", "성명": "단비", "권역": "영미권", "실매출액": 50183723, "인센티브": 250920},
    {"월": "3월", "성명": "장원희", "권역": "일본", "실매출액": 95387311, "인센티브": 953880},
]

df = pd.DataFrame(data)

# 2. 상단 요약 지표
total_sales = df['실매출액'].sum()
total_inc = df['인센티브'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("1분기 총 실매출", f"{total_sales:,}원")
col2.metric("1분기 총 인센티브", f"{total_inc:,}원")
col3.metric("평균 지급율", f"{(total_inc/total_sales*100):.2f}%")

st.divider()

# 3. 차트 시각화
c1, c2 = st.columns(2)

with c1:
    st.subheader("📅 월별 인센티브 현황")
    fig1 = px.bar(df.groupby("월")["인센티브"].sum().reset_index(), 
                  x="월", y="인센티브", text_auto=',.0f', color_discrete_sequence=['#1f77b4'])
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    st.subheader("🌍 권역별 실적 비중")
    fig2 = px.pie(df, values="실매출액", names="권역", hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

# 4. 상세 테이블
st.subheader("📂 세부 지급 내역")
st.dataframe(df.style.format({"실매출액": "{:,}", "인센티브": "{:,}"}), use_container_width=True)