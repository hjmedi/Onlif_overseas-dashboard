import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 매출 분석", layout="wide")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"

# 🌍 국가별 권역 매핑 (업데이트됨)
def get_region(nation):
    nation = str(nation).strip()
    if nation in ['중국', '대만', '홍콩', '마카오', 'China', 'Taiwan', 'Hong Kong']:
        return '중화권'
    elif nation in ['일본', 'Japan']:
        return '일본'
    elif nation in ['태국', '베트남', '싱가포르', '필리핀', '말레이시아', '인도네시아', '미얀마', '캄보디아', '라오스', 'Singapore', 'Thailand', 'Vietnam', 'Malaysia']:
        return '동남아'
    elif nation in ['미국', '캐나다', 'USA', 'Canada', 'United States']:
        return '북미'
    elif nation in ['영국', '프랑스', '독일', '이탈리아', '스페인', '러시아', '네덜란드', 'UK', 'France', 'Germany']:
        return '유럽'
    else:
        return '기타'

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
    try: return float(s) / 1.1
    except: return 0

raw_data = get_data(CSV_URL)

if raw_data is not None:
    header_idx = 0
    for i in range(len(raw_data)):
        row_str = " ".join(raw_data.iloc[i].fillna('').astype(str))
        if '이름' in row_str and '국적' in row_str:
            header_idx = i
            break
    
    df = raw_data.copy()
    df.columns = [str(c).strip() for c in df.iloc[header_idx].fillna('미지정')]
    df = df.drop(range(header_idx + 1)).reset_index(drop=True)

    # 필터링 및 계산
    filter_col = [c for c in df.columns if '국내' in c or '해외' in c or '구분' in c]
    if filter_col:
        df = df[df[filter_col[0]].astype(str).str.contains('해외', na=False)]

    amt_col = [c for c in df.columns if '수납액' in c and 'CRM' in c]
    if not amt_col: amt_col = [c for c in df.columns if '수납액' in c or '금액' in c]
    df['매출액_숫자'] = df[amt_col[0]].apply(to_numeric_net) if amt_col else 0
    df['권역'] = df['국적'].apply(get_region)

    date_col = [c for c in df.columns if '수납일' in c]
    if date_col:
        df['날짜형식'] = pd.to_datetime(df[date_col[0]], errors='coerce')
        df = df.dropna(subset=['날짜형식'])
        df['월날짜'] = df['날짜형식'].dt.to_period('M').dt.to_timestamp()
        df['매출월'] = df['날짜형식'].dt.strftime('%y년 %m월')

    # 사이드바
    st.sidebar.header("📊 조회 설정")
    sidebar_df = df[['월날짜', '매출월']].drop_duplicates().sort_values('월날짜', ascending=False)
    selected_month = st.sidebar.selectbox("📅 조회할 월 선택", sidebar_df['매출월'].tolist())
    view_mode = st.sidebar.radio("🔎 분석 기준 선택", ["국가별", "권역별"])
    group_col = '국적' if view_mode == "국가별" else '권역'

    filtered_df = df[df['매출월'] == selected_month]
    month_revenue = filtered_df['매출액_숫자'].sum()

    st.title(f"📊 온리프 해외매출 {view_mode} 분석")
    st.header(f"{month_revenue:,.0f}원")
    st.divider()

    # 상단 그래프 및 표
    c1, c2 = st.columns([1, 1.2])
    with c1:
        n_df = filtered_df.groupby(group_col)['매출액_숫자'].sum().reset_index()
        fig_pie = px.pie(n_df, values='매출액_숫자', names=group_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    with c2:
        table_df = n_df.sort_values(by='매출액_숫자', ascending=False).reset_index(drop=True)
        table_df['매출액'] = table_df['매출액_숫자'].map('{:,.0f}'.format)
        st.table(table_df[[group_col, '매출액']])

    # 🔍 '기타' 권역 구성 국가 확인용 섹션
    st.divider()
    st.subheader("❓ '기타' 권역은 어떤 국가인가요?")
    etc_nations = filtered_df[filtered_df['권역'] == '기타']['국적'].unique()
    if len(etc_nations) > 0:
        st.write(f"현재 **{selected_month}** 기준 '기타'로 분류된 국가: ")
        st.info(", ".join(etc_nations))
    else:
        st.write("해당 월에는 '기타'로 분류된 국가가 없습니다.")

    # 하단 추이
    st.subheader(f"📈 월별 성장 추이 ({view_mode})")
    trend_raw = df.groupby(['월날짜', '매출월', group_col])['매출액_숫자'].sum().reset_index()
    total_trend = df.groupby(['월날짜', '매출월'])['매출액_숫자'].sum().reset_index()
    sorted_months = total_trend.sort_values('월날짜')['매출월'].tolist()

    fig_trend = go.Figure()
    for item in trend_raw[group_col].unique():
        item_data = trend_raw[trend_raw[group_col] == item].sort_values('월날짜')
        fig_trend.add_trace(go.Bar(x=item_data['매출월'], y=item_data['매출액_숫자'], name=item, text=item, textposition='auto'))

    fig_trend.update_layout(barmode='stack', xaxis={'categoryorder': 'array', 'categoryarray': sorted_months})
    st.plotly_chart(fig_trend, use_container_width=True)

else:
    st.error("데이터 로딩 실패")
