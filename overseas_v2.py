import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 매출 통합 대시보드", layout="wide")

# ✅ 데이터 주소 설정
URL_MAIN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"
COMMISSION_URLS = [
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1298456060&single=true&output=csv", # 10월
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=344598450&single=true&output=csv",  # 11월
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1973655230&single=true&output=csv", # 12월
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2053307016&single=true&output=csv"  # 1월
]

# 🌍 권역 매핑 함수
def get_region(nation):
    nation = str(nation).strip()
    if nation in ['중국', '대만', '홍콩', '마카오', 'China', 'Taiwan', 'Hong Kong']: return '중화권'
    elif nation in ['일본', 'Japan']: return '일본'
    elif nation in ['태국', '베트남', '싱가포르', '필리핀', '말레이시아', '인도네시아', 'Singapore', 'Thailand']: return '동남아'
    elif nation in ['미국', '캐나다', 'USA', 'Canada']: return '북미'
    elif nation in ['영국', '프랑스', '독일', '러시아', 'Russia', 'France', 'Germany']: return '유럽'
    else: return '기타'

def to_numeric(val):
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

@st.cache_data(ttl=30)
def load_all_data():
    # 메인 시트 로드
    res = requests.get(URL_MAIN)
    df_main = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
    
    # 수수료 시트 통합 로드
    all_comm_dfs = []
    for url in COMMISSION_URLS:
        try:
            r = requests.get(url)
            tmp_df = pd.read_csv(StringIO(r.content.decode('utf-8-sig')))
            all_comm_dfs.append(tmp_df)
        except: continue
    df_comm = pd.concat(all_comm_dfs, ignore_index=True) if all_comm_dfs else pd.DataFrame()
    
    return df_main, df_comm

raw_main, df_comm = load_all_data()

# --- 데이터 전처리 ---
header_idx = 0
for i in range(len(raw_main)):
    row_str = " ".join(raw_main.iloc[i].fillna('').astype(str))
    if '이름' in row_str and '국적' in row_str:
        header_idx = i
        break
df_main = raw_main.copy()
df_main.columns = [str(c).strip() for c in df_main.iloc[header_idx].fillna('미지정')]
df_main = df_main.drop(range(header_idx + 1)).reset_index(drop=True)
df_main = df_main[df_main['구분'].astype(str).str.contains('해외', na=False)]
df_main['매출액_숫자'] = df_main['수납액(CRM)'].apply(to_numeric) / 1.1
df_main['날짜형식'] = pd.to_datetime(df_main['수납일'], errors='coerce')
df_main = df_main.dropna(subset=['날짜형식'])
df_main['매출월'] = df_main['날짜형식'].dt.strftime('%y년 %m월')
df_main['권역'] = df_main['국적'].apply(get_region)

# 수수료 데이터 전처리
if not df_comm.empty:
    df_comm['수납액_숫자'] = df_comm['수납액'].apply(to_numeric)
    df_comm['수수료_숫자'] = df_comm['수수료(정산금)'].apply(to_numeric)
    df_comm['날짜형식'] = pd.to_datetime(df_comm['수납일'], errors='coerce')
    df_comm = df_comm.dropna(subset=['날짜형식'])
    df_comm['매출월'] = df_comm['날짜형식'].dt.strftime('%y년 %m월')

# --- 사이드바 메뉴 ---
st.sidebar.title("🏨 온리프 대시보드")
menu = st.sidebar.radio("메뉴 선택", ["🌐 전체 매출 요약", "💸 수수료 매출 분석"])
selected_month = st.sidebar.selectbox("📅 조회 월 선택", sorted(df_main['매출월'].unique(), reverse=True))

# --- [메뉴 1] 전체 매출 요약 ---
if menu == "🌐 전체 매출 요약":
    st.title("🌐 국적 및 권역별 매출 요약")
    view_mode = st.sidebar.radio("🔎 분석 기준", ["국가별", "권역별"])
    group_col = '국적' if view_mode == "국가별" else '권역'
    
    m_df = df_main[df_main['매출월'] == selected_month]
    total_rev = m_df['매출액_숫자'].sum()
    st.metric(f"{selected_month} 총 매출 (공급가)", f"{total_rev:,.0f}원")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        n_df = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index()
        fig = px.pie(n_df, values='매출액_숫자', names=group_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader(f"📑 {view_mode} 상세 실적")
        table_df = n_df.sort_values('매출액_숫자', ascending=False)
        table_df['매출액'] = table_df['매출액_숫자'].apply(lambda x: f"{int(x):,}")
        st.dataframe(table_df[[group_col, '매출액']], use_container_width=True, hide_index=True,
                     column_config={"매출액": st.column_config.TextColumn(alignment="right")})

# --- [메뉴 2] 수수료 매출 분석 ---
else:
    st.title("💸 수수료 및 정산금 분석")
    if not df_comm.empty:
        c_df = df_comm[df_comm['매출월'] == selected_month]
        
        t_rev = c_df['수납액_숫자'].sum()
        t_fee = c_df['수수료_숫자'].sum()
        net_rev = t_rev - t_fee
        fee_rate = (t_fee / t_rev * 100) if t_rev > 0 else 0
        
        # 상단 지표
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 수납액", f"{t_rev:,.0f}원")
        m2.metric("총 수수료", f"{t_fee:,.0f}원", delta=f"-{fee_rate:.1f}%", delta_color="inverse")
        m3.metric("실 매출액(수익)", f"{net_rev:,.0f}원")
        m4.metric("평균 수수료율", f"{fee_rate:.1f}%")
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("🔗 유입 경로별 수수료 비중")
            path_df = c_df.groupby('유입경로')['수수료_숫자'].sum().reset_index()
            fig_path = px.pie(path_df, values='수수료_숫자', names='유입경로', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_path, use_container_width=True)
            
        with col2:
            st.subheader("📈 월별 수수료 추이")
            trend_df = df_comm.groupby('매출월').agg({'수납액_숫자':'sum', '수수료_숫자':'sum'}).reset_index()
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(x=trend_df['매출월'], y=trend_df['수납액_숫자'], name='총 수납액'))
            fig_trend.add_trace(go.Bar(x=trend_df['매출월'], y=trend_df['수수료_숫자'], name='수수료'))
            fig_trend.update_layout(barmode='group')
            st.plotly_chart(fig_trend, use_container_width=True)

        st.subheader("📑 수수료 상세 내역")
        c_df_display = c_df[['수납일', '이름', '유입경로', '수납액_숫자', '수수료_숫자']].copy()
        c_df_display['수납액'] = c_df_display['수납액_숫자'].apply(lambda x: f"{int(x):,}")
        c_df_display['수수료'] = c_df_display['수수료_숫자'].apply(lambda x: f"{int(x):,}")
        st.dataframe(c_df_display[['수납일', '이름', '유입경로', '수납액', '수수료']], use_container_width=True, hide_index=True,
                     column_config={"수납액": st.column_config.TextColumn(alignment="right"), "수수료": st.column_config.TextColumn(alignment="right")})
    else:
        st.warning("수수료 데이터를 불러올 수 없습니다.")
