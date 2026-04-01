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

# 🌍 권역 매핑 함수
def get_region(nation):
    nation = str(nation).strip()
    if nation in ['중국', '대만', '홍콩', '마카오', 'China', 'Taiwan', 'Hong Kong']: return '중화권'
    elif nation in ['일본', 'Japan']: return '일본'
    elif nation in ['태국', '베트남', '싱가포르', '필리핀', '말레이시아', '인도네시아', '미얀마', '캄보디아', '라오스']: return '동남아'
    elif nation in ['미국', '캐나다', 'USA', 'Canada', 'United States']: return '북미'
    elif nation in ['영국', '프랑스', '독일', '이탈리아', '스페인', '러시아', '네덜란드']: return '유럽'
    else: return '기타'

def to_numeric(val):
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

@st.cache_data(ttl=30)
def load_all_data():
    # 1. 메인 매출 데이터
    res_m = requests.get(URL_MAIN)
    df_m_raw = pd.read_csv(StringIO(res_m.content.decode('utf-8-sig')), header=None)
    
    h_idx = 0
    for i in range(len(df_m_raw)):
        if '이름' in "".join(df_m_raw.iloc[i].fillna('').astype(str)):
            h_idx = i; break
            
    df_m = df_m_raw.copy()
    df_m.columns = [str(c).strip() for c in df_m.iloc[h_idx].fillna('미지정')]
    df_m = df_m.drop(range(h_idx + 1)).reset_index(drop=True)
    
    div_col = [c for c in df_m.columns if '구분' in c or '해외' in c]
    if div_col:
        df_m = df_m[df_m[div_col[0]].astype(str).str.contains('해외', na=False)]
        
    amt_col = [c for c in df_m.columns if '수납액' in c and 'CRM' in c]
    if not amt_col: amt_col = [c for c in df_m.columns if '수납액' in c]
    df_m['매출액_숫자'] = df_m[amt_col[0]].apply(to_numeric) / 1.1 if amt_col else 0
    df_m['권역'] = df_m['국적'].apply(get_region)
    
    # 2. 수수료 데이터
    comm_list = []
    for name, url in COMMISSION_URLS.items():
        try:
            r = requests.get(url)
            temp = pd.read_csv(StringIO(r.content.decode('utf-8-sig')))
            df_c = pd.DataFrame({
                '에이전트': name,
                '국적': temp.iloc[:, 3],
                '날짜': temp.iloc[:, 4],
                '매출액': temp.iloc[:, 8].apply(to_numeric)
            })
            comm_list.append(df_c)
        except: continue
    df_comm_total = pd.concat(comm_list, ignore_index=True) if comm_list else pd.DataFrame()
    
    return df_m, df_comm_total

df_main_raw, df_comm_raw = load_all_data()

# --- 날짜 처리 함수 (YYYY-MM 형식의 월순서) ---
def format_date(df, col):
    target_col = [c for c in df.columns if col in c]
    if target_col:
        df['날짜형'] = pd.to_datetime(df[target_col[0]], errors='coerce')
        df = df.dropna(subset=['날짜형'])
        df['매출월'] = df['날짜형'].dt.strftime('%y년 %m월')
        df['월순서'] = df['날짜형'].dt.strftime('%Y-%m') # 정렬키
    return df

df_main = format_date(df_main_raw, '수납일')
df_comm = format_date(df_comm_raw, '날짜')

# 메인 시트와 수수료 시트의 모든 날짜 합쳐서 오름차순 리스트 생성
all_dates_df = pd.concat([
    df_main[['월순서', '매출월']] if not df_main.empty and '월순서' in df_main.columns else pd.DataFrame(),
    df_comm[['월순서', '매출월']] if not df_comm.empty and '월순서' in df_comm.columns else pd.DataFrame()
]).drop_duplicates().sort_values('월순서')

CHRONOLOGICAL_MONTHS = all_dates_df['매출월'].dropna().tolist()

# --- 사이드바 ---
st.sidebar.title("🏨 온리프 관리 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🌐 전체 매출 요약", "💸 수수료 매출(에이전트별)"])

# 선택박스는 최신순으로
month_list = sorted(CHRONOLOGICAL_MONTHS, reverse=True)

if not month_list:
    st.error("데이터에서 날짜 정보를 찾을 수 없습니다.")
else:
    sel_month = st.sidebar.selectbox("📅 조회 월 선택", month_list)

    # ==========================================================
    # --- 메뉴 1: 전체 매출 요약 ---
    # ==========================================================
    if menu == "🌐 전체 매출 요약":
        st.title(f"🌐 {sel_month} 전체 매출 요약")
        view_mode = st.sidebar.radio("🔎 분석 기준", ["국가별", "권역별"])
        group_col = '국적' if view_mode == "국가별" else '권역'

        if '매출월' in df_main.columns:
            m_df = df_main[df_main['매출월'] == sel_month]
            total_rev = m_df['매출액_숫자'].sum()
            st.metric("총 매출액 (VAT 제외)", f"{total_rev:,.0f}원")

            c1, c2 = st.columns([1, 1.2])
            with c1:
                n_df = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index()
                fig_pie = px.pie(n_df, values='매출액_숫자', names=group_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.subheader(f"📑 {view_mode} 상세 실적")
                st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>(단위: 원)</p>", unsafe_allow_html=True)
                table_df = n_df.sort_values('매출액_숫자', ascending=False)
                table_df['매출액(원)'] = table_df['매출액_숫자'].apply(lambda x: f"{int(x):,}")
                st.dataframe(table_df[[group_col, '매출액(원)']], use_container_width=True, hide_index=True, column_config={"매출액(원)": st.column_config.TextColumn(alignment="right")})

            st.divider()
            st.subheader(f"📈 전체 월별 성장 추이 ({view_mode} 기준)")
            trend_df = df_main.groupby(['월순서', '매출월', group_col])['매출액_숫자'].sum().reset_index().sort_values('월순서')
            fig_trend = go.Figure()
            for item in trend_df[group_col].unique():
                item_data = trend_df[trend_df[group_col] == item]
                fig_trend.add_trace(go.Bar(x=item_data['매출월'], y=item_data['매출액_숫자'], name=item, text=item, textposition='auto'))
            
            total_trend = df_main.groupby(['월순서', '매출월'])['매출액_숫자'].sum().reset_index().sort_values('월순서')
            fig_trend.add_trace(go.Scatter(x=total_trend['매출월'], y=total_trend['매출액_숫자'], name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}M" for v in total_trend['매출액_숫자']], textposition="top center"))
            
            fig_trend.update_layout(
                barmode='stack', hovermode="x unified",
                xaxis={'categoryorder': 'array', 'categoryarray': CHRONOLOGICAL_MONTHS}
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.warning("메인 매출 데이터가 없습니다.")

    # ==========================================================
    # --- 메뉴 2: 수수료 매출 (에이전트별) ---
    # ==========================================================
    else:
        st.title(f"💸 수수료 매출 (에이전트별) 분석")
        
        if not df_comm.empty:
            st.subheader("📈 월별 수수료 매출 전체 추이")
            trend_data = df_comm.groupby(['월순서', '매출월', '에이전트'])['매출액'].sum().reset_index().sort_values('월순서')
            
            fig_ctrend = go.Figure()
            agents = trend_data['에이전트'].unique()
            for agent in agents:
                a_data = trend_data[trend_data['에이전트'] == agent]
                fig_ctrend.add_trace(go.Bar(x=a_data['매출월'], y=a_data['매출액'], name=agent, text=agent, textposition='auto'))
            
            total_cline = trend_data.groupby('매출월')['매출액'].sum().reindex(CHRONOLOGICAL_MONTHS).dropna()
            fig_ctrend.add_trace(go.Scatter(x=total_cline.index, y=total_cline.values, name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}M" for v in total_cline.values], textposition="top center"))
            
            fig_ctrend.update_layout(
                barmode='stack', hovermode="x unified", height=500,
