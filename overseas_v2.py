import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 매출 분석 대시보드", layout="wide")

# ✅ 수납raw 시트 CSV 주소
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url)
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
        return df
    except: return None

def to_numeric_net(val):
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: 
        return float(s) / 1.1
    except: return 0

raw_data = get_data(CSV_URL)

if raw_data is not None:
    # --- 제목줄 찾기 ---
    header_idx = 0
    for i in range(len(raw_data)):
        row_str = " ".join(raw_data.iloc[i].fillna('').astype(str))
        if '이름' in row_str and '국적' in row_str:
            header_idx = i
            break
    
    df = raw_data.copy()
    df.columns = [str(c).strip() for c in df.iloc[header_idx].fillna('미지정')]
    df = df.drop(range(header_idx + 1)).reset_index(drop=True)

    # 1️⃣ 해외 데이터 필터링
    filter_col = [c for c in df.columns if '국내' in c or '해외' in c or '구분' in c]
    if filter_col:
        df = df[df[filter_col[0]].astype(str).str.contains('해외', na=False)]

    # 2️⃣ 매출액 계산 (1.1 반영)
    amt_col = [c for c in df.columns if '수납액' in c and 'CRM' in c]
    if not amt_col:
        amt_col = [c for c in df.columns if '수납액' in c or '금액' in c]
    df['매출액_숫자'] = df[amt_col[0]].apply(to_numeric_net) if amt_col else 0

    # 3️⃣ 날짜 처리
    date_col = [c for c in df.columns if '수납일' in c]
    if date_col:
        df['날짜형식'] = pd.to_datetime(df[date_col[0]], errors='coerce')
        df = df.dropna(subset=['날짜형식'])
        
        # 월의 첫날로 통일 (정렬용 표준 날짜 생성)
        df['월날짜'] = df['날짜형식'].dt.to_period('M').dt.to_timestamp()
        # 화면 표시용 텍스트
        df['매출월'] = df['날짜형식'].dt.strftime('%y년 %m월')

    # --- 사이드바 설정 ---
    st.sidebar.header("📊 메뉴 이동")
    st.sidebar.radio("리스트 선택:", ["🌐 전체 매출 요약 (원형 그래프)"])
    
    # 사이드바 목록 (날짜순 정렬)
    sidebar_df = df[['월날짜', '매출월']].drop_duplicates().sort_values('월날짜', ascending=False)
    selected_month = st.sidebar.selectbox("📅 조회할 월 선택", sidebar_df['매출월'].tolist())

    # --- 데이터 필터링 ---
    filtered_df = df[df['매출월'] == selected_month]
    month_revenue = filtered_df['매출액_숫자'].sum()

    # --- 상단 분석 영역 ---
    st.title(f"📊 온리프 해외매출 국적별 비중 분석")
    st.caption(f"📍 {selected_month} 해외매출 종합 (공급가 기준)")
    st.header(f"{month_revenue:,.0f}원")
    st.divider()

    if not filtered_df.empty:
        c1, c2 = st.columns([1, 1.2])
        with c1:
            n_df = filtered_df.groupby('국적')['매출액_숫자'].sum().reset_index()
            fig_pie = px.pie(n_df, values='매출액_숫자', names='국적', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Bold)
            fig_pie.update_traces(textinfo='percent+label', texttemplate='%{label}<br>%{percent}')
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            st.subheader(f"📑 {selected_month} 국적별 상세 실적")
            table_df = n_df.sort_values(by='매출액_숫자', ascending=False).reset_index(drop=True)
            table_df['비중'] = (table_df['매출액_숫자'] / month_revenue * 100).map('{:.1f}%'.format)
            table_df['매출액'] = table_df['매출액_숫자'].map('{:,.0f}'.format)
            st.table(table_df[['국적', '매출액', '비중']])

    # --- 하단 성장 추이 ---
    st.divider()
    st.subheader("📈 전체 해외매출 월별 성장 추이 (국적별 구성)")
    
    # 월(표준날짜) 기준으로 데이터 그룹화
    trend_raw = df.groupby(['월날짜', '매출월', '국적'])['매출액_숫자'].sum().reset_index()
    total_trend = df.groupby(['월날짜', '매출월'])['매출액_숫자'].sum().reset_index()

    # X축 순서 강제 고정용 리스트
    sorted_months = total_trend.sort_values('월날짜')['매출월'].tolist()

    fig_trend = go.Figure()

    # 1. 막대 그래프 (국적별 쌓기 + 🔥 국가 이름 표시 추가)
    for nation in trend_raw['국적'].unique():
        n_data = trend_raw[trend_raw['국적'] == nation].sort_values('월날짜')
        fig_trend.add_trace(go.Bar(
            x=n_data['매출월'], 
            y=n_data['매출액_숫자'], 
            name=nation,
            text=nation, # 🔥 막대 안에 표시할 텍스트로 국가 이름 지정
            textposition='auto', # 🔥 텍스트 위치 자동 (막대 크기에 따라 안쪽 또는 바깥쪽)
            textfont=dict(color='white') # 🔥 텍스트 색상 설정 (배경색에 따라 조정 필요할 수 있음)
        ))

    # 2. 선 그래프 (합계 추세선)
    total_trend = total_trend.sort_values('월날짜')
    fig_trend.add_trace(go.Scatter(
        x=total_trend['매출월'], y=total_trend['매출액_숫자'],
        name='해외매출 총합', line=dict(color='black', width=3),
        mode='lines+markers+text',
        text=[f"{v/1000000:.1f}M" for v in total_trend['매출액_숫자']],
        textposition="top center"
    ))

    fig_trend.update_layout(
        barmode='stack',
        xaxis={'categoryorder': 'array', 'categoryarray': sorted_months}, # 정렬된 리스트 순서대로 강제 고정
        hovermode="x unified"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.error("데이터 로딩 실패")
