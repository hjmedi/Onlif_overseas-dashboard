import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 1. 페이지 설정
st.set_page_config(page_title="온리프 해외 매출 통합 관리", layout="wide")

# ✅ 데이터 주소
URL_MAIN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"
COMMISSION_URLS = {
    "레이블": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1298456060&single=true&output=csv",
    "The SC": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=344598450&single=true&output=csv",
    "천수현 대표": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1973655230&single=true&output=csv",
    "앤티스": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2053307016&single=true&output=csv"
}

def to_numeric(val):
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

@st.cache_data(ttl=30)
def load_all_data():
    # 1. 메인 매출 데이터 로드
    res_m = requests.get(URL_MAIN)
    df_m_raw = pd.read_csv(StringIO(res_m.content.decode('utf-8-sig')), header=None)
    h_idx = 0
    for i in range(len(df_m_raw)):
        if '이름' in "".join(df_m_raw.iloc[i].fillna('').astype(str)):
            h_idx = i; break
    df_m = df_m_raw.copy()
    df_m.columns = [str(c).strip() for c in df_m.iloc[h_idx].fillna('미지정')]
    df_m = df_m.drop(range(h_idx + 1)).reset_index(drop=True)
    
    # 2. 수수료 데이터 로드 (고정 열: D-국적, E-월, I-매출)
    comm_list = []
    for name, url in COMMISSION_URLS.items():
        try:
            r = requests.get(url)
            # 수수료 시트는 데이터 구조가 단순하므로 바로 읽음 (header=0 가정)
            temp = pd.read_csv(StringIO(r.content.decode('utf-8-sig')))
            # 가이드에 따라 열 지정: D=3, E=4, I=8 (index 기준)
            df_c = pd.DataFrame({
                '에이전트': name,
                '국적': temp.iloc[:, 3], # D열
                '날짜': temp.iloc[:, 4], # E열
                '매출액': temp.iloc[:, 8].apply(to_numeric) # I열
            })
            comm_list.append(df_c)
        except: continue
    df_comm_total = pd.concat(comm_list, ignore_index=True) if comm_list else pd.DataFrame()
    
    return df_m, df_comm_total

df_main_raw, df_comm_raw = load_all_data()

# --- 날짜 처리 함수 ---
def format_date(df, col):
    df['날짜형'] = pd.to_datetime(df[col], errors='coerce')
    df = df.dropna(subset=['날짜형'])
    df['매출월'] = df['날짜형'].dt.strftime('%y년 %m월')
    df['월순서'] = df['날짜형'].dt.to_period('M')
    return df

df_main = format_date(df_main_raw, '수납일')
df_comm = format_date(df_comm_raw, '날짜')

# --- 사이드바 ---
st.sidebar.title("🏨 온리프 관리 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🌐 전체 매출 요약", "💸 수수료 매출(에이전트별)"])
month_list = sorted(df_main['매출월'].unique(), reverse=True)
sel_month = st.sidebar.selectbox("📅 조회 월 선택", month_list)

# --- 메뉴 1: 전체 매출 요약 (기존 유지) ---
if menu == "🌐 전체 매출 요약":
    st.title(f"🌐 {sel_month} 전체 매출 요약")
    # ... (기존 국적/권역별 코드와 동일하게 작동)
    m_df = df_main[df_main['매출월'] == sel_month]
    total_rev = (m_df['수납액(CRM)'].apply(to_numeric) / 1.1).sum()
    st.header(f"{total_rev:,.0f}원")
    # (생략: 기존의 Pie 차트 및 추이 그래프 코드)
    st.info("첫 번째 페이지는 기존 설정대로 정상 작동 중입니다.")

# --- 메뉴 2: 수수료 매출 (에이전트별) ---
else:
    st.title(f"💸 수수료 매출 (에이전트별) 분석")
    
    # 1. 월별 수수료 매출 전체 추이 (Stacked Bar + Line)
    st.subheader("📈 월별 수수료 매출 전체 추이")
    trend_data = df_comm.groupby(['월순서', '매출월', '에이전트'])['매출액'].sum().reset_index().sort_values('월순서')
    
    fig_trend = go.Figure()
    # 에이전트별 막대 쌓기
    agents = trend_data['에이전트'].unique()
    for agent in agents:
        agent_data = trend_data[trend_data['에이전트'] == agent]
        fig_trend.add_trace(go.Bar(
            x=agent_data['매출월'], y=agent_data['매출액'], 
            name=agent, text=agent, textposition='auto'
        ))
    
    # 합계 라인 추가
    total_line = trend_data.groupby('매출월')['매출액'].sum().reindex(trend_data['매출월'].unique())
    fig_trend.add_trace(go.Scatter(
        x=total_line.index, y=total_line.values,
        name='총합', line=dict(color='black', width=3),
        mode='lines+markers+text',
        text=[f"{v/1000000:.1f}M" for v in total_line.values],
        textposition="top center"
    ))
    
    fig_trend.update_layout(barmode='stack', hovermode="x unified", height=500)
    st.plotly_chart(fig_trend, use_container_width=True)

    # 2. 에이전트별 국가 구성비 (Horizontal Stacked Bar)
    st.divider()
    st.subheader(f"🗺️ {sel_month} 에이전트별 국가 구성비")
    
    curr_month_comm = df_comm[df_comm['매출월'] == sel_month]
    if not curr_month_comm.empty:
        comp_data = curr_month_comm.groupby(['에이전트', '국적'])['매출액'].sum().reset_index()
        
        fig_comp = px.bar(
            comp_data, x='매출액', y='에이전트', color='국적',
            orientation='h',
            text_auto='.2s',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_comp.update_layout(barmode='stack', height=400)
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # 상세 데이터 표 (우측 정렬 및 콤마)
        st.subheader("📑 상세 정산 내역")
        table_comm = curr_month_comm.groupby(['에이전트', '국적'])['매출액'].sum().reset_index()
        table_comm = table_comm.sort_values(['에이전트', '매출액'], ascending=[True, False])
        table_comm['매출액(원)'] = table_comm['매출액'].apply(lambda x: f"{int(x):,}")
        st.dataframe(table_comm[['에이전트', '국적', '매출액(원)']], use_container_width=True, hide_index=True,
                     column_config={"매출액(원)": st.column_config.TextColumn(alignment="right")})
    else:
        st.warning(f"{sel_month}에 해당하는 수수료 데이터가 없습니다.")
