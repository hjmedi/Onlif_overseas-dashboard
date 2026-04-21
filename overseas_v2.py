import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 1. 페이지 설정
st.set_page_config(page_title="온리프 해외 매출 통합 관리", layout="wide")

# ✅ 데이터 주소 및 수수료율 설정
URL_MAIN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"
COMMISSION_URLS = {
    "레이블": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1298456060&single=true&output=csv",
    "The SC": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=344598450&single=true&output=csv",
    "천수현 대표": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1973655230&single=true&output=csv",
    "앤티스": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2053307016&single=true&output=csv",
    "크리에이트립": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2000088021&single=true&output=csv"
}

# 에이전트별 수수료율 정의 (기본값 15%, 크리에이트립 11%)
COMMISSION_RATES = {
    "레이블": 0.15,
    "The SC": 0.15,
    "천수현 대표": 0.15,
    "앤티스": 0.15, 
    "크리에이트립": 0.11
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

# 🔥 축 단위 '백' 자동 생성 함수
def get_dynamic_ticks(max_val):
    if pd.isna(max_val) or max_val == 0: return [0], ["0"]
    if max_val >= 100000000: step = 50000000      # 1억 이상이면 5천만 단위
    elif max_val >= 50000000: step = 20000000    # 5천만 이상이면 2천만 단위
    elif max_val >= 20000000: step = 10000000    # 2천만 이상이면 1천만 단위
    elif max_val >= 10000000: step = 5000000     # 1천만 이상이면 5백만 단위
    else: step = 2000000                         # 그 이하는 2백만 단위
    
    vals = list(range(0, int(max_val) + step*2, step))
    txts = [f"{v/1000000:g}백" if v != 0 else "0" for v in vals]
    return vals, txts

@st.cache_data(ttl=30)
def load_all_data():
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
            
            # 🔥 크리에이트립인 경우 국적이 '중국'인 데이터만 남기도록 필터링
            if name == "크리에이트립":
                df_c = df_c[df_c['국적'].astype(str).str.contains('중국', na=False)]
                
            comm_list.append(df_c)
        except: continue
        
    df_comm_total = pd.concat(comm_list, ignore_index=True) if comm_list else pd.DataFrame()
    
    # 🔥 에이전트별 수수료 및 실매출액 계산 로직 추가
    if not df_comm_total.empty:
        df_comm_total['수수료율'] = df_comm_total['에이전트'].map(COMMISSION_RATES).fillna(0.15)
        df_comm_total['지급수수료'] = df_comm_total['매출액'] * df_comm_total['수수료율']
        df_comm_total['실매출액'] = df_comm_total['매출액'] - df_comm_total['지급수수료']
        
    return df_m, df_comm_total

df_main_raw, df_comm_raw = load_all_data()

def format_date(df, col):
    target_col = [c for c in df.columns if col in c]
    if target_col:
        df['날짜형'] = pd.to_datetime(df[target_col[0]], errors='coerce')
        df = df.dropna(subset=['날짜형'])
        df['매출월'] = df['날짜형'].dt.strftime('%y년 %m월')
        df['월순서'] = df['날짜형'].dt.strftime('%Y-%m')
    return df

df_main = format_date(df_main_raw, '수납일')
df_comm = format_date(df_comm_raw, '날짜')

all_dates_df = pd.concat([
    df_main[['월순서', '매출월']] if not df_main.empty and '월순서' in df_main.columns else pd.DataFrame(),
    df_comm[['월순서', '매출월']] if not df_comm.empty and '월순서' in df_comm.columns else pd.DataFrame()
]).drop_duplicates().sort_values('월순서')
CHRONOLOGICAL_MONTHS = all_dates_df['매출월'].dropna().tolist()

# 🔥 대시보드 전체의 일관된 차트 색상을 위한 전역 Color Map 생성 
extended_colors = (
    px.colors.qualitative.Pastel + 
    px.colors.qualitative.Set3 + 
    px.colors.qualitative.Set2 + 
    px.colors.qualitative.Safe
) * 10 

all_nations = sorted(pd.concat([df_main['국적'] if not df_main.empty else pd.Series(), df_comm['국적'] if not df_comm.empty else pd.Series()]).dropna().unique())
NATION_COLOR_MAP = {nation: extended_colors[i] for i, nation in enumerate(all_nations)}

# 🎯 중국 및 일본 색상 명시적 고정 (눈이 편안한 파스텔 톤)
if '중국' in NATION_COLOR_MAP:
    NATION_COLOR_MAP['중국'] = '#81C784' # 파스텔 초록색
if '일본' in NATION_COLOR_MAP:
    NATION_COLOR_MAP['일본'] = '#64B5F6' # 파스텔 파란색

all_regions = sorted(df_main['권역'].dropna().unique()) if not df_main.empty else []
REGION_COLOR_MAP = {region: extended_colors[i] for i, region in enumerate(all_regions)}

all_agents = sorted(df_comm['에이전트'].dropna().unique()) if not df_comm.empty else []
AGENT_COLOR_MAP = {agent: extended_colors[i] for i, agent in enumerate(all_agents)}


# 🔥 사이드바 타이틀 수정
st.sidebar.title("🏨 온리프 해외 매출")
menu = st.sidebar.radio("메뉴 이동", ["🌐 온리프 해외매출 전체", "💸 수수료 매출(에이전트별)"])
month_list = sorted(CHRONOLOGICAL_MONTHS, reverse=True)

if not month_list:
    st.error("데이터에서 날짜 정보를 찾을 수 없습니다.")
else:
    # ==========================================================
    # --- 🎛️ 기간 조회 및 필터 설정 ---
    # ==========================================================
    # 1. 기존 상세 조회 월 선택 (상단 요약 카드용)
    sel_month = st.sidebar.selectbox("📅 상세 조회 월 선택", month_list)

    # 2. 신규 다중 기간 검색 슬라이더 (트렌드 차트용)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 트렌드 차트 기간 설정")
    
    # 기본값 설정: 최근 6개월 (데이터가 6개월 미만이면 전체)
    default_start = CHRONOLOGICAL_MONTHS[-6] if len(CHRONOLOGICAL_MONTHS) >= 6 else CHRONOLOGICAL_MONTHS[0]
    default_end = CHRONOLOGICAL_MONTHS[-1]

    start_month, end_month = st.sidebar.select_slider(
        "조회할 기간(시작월 - 종료월)을 선택하세요",
        options=CHRONOLOGICAL_MONTHS,
        value=(default_start, default_end)
    )

    # 선택된 기간에 해당하는 월 리스트 추출
    start_idx = CHRONOLOGICAL_MONTHS.index(start_month)
    end_idx = CHRONOLOGICAL_MONTHS.index(end_month)
    FILTERED_MONTHS = CHRONOLOGICAL_MONTHS[start_idx : end_idx + 1]

    # ==========================================================
    # --- 메뉴 1: 온리프 해외매출 전체 ---
    # ==========================================================
    if menu == "🌐 온리프 해외매출 전체":
        st.title(f"🌐 {sel_month} 온리프 해외매출 전체")
        view_mode = st.sidebar.radio("🔎 분석 기준", ["국가별", "권역별"])
        group_col = '국적' if view_mode == "국가별" else '권역'
        current_color_map = NATION_COLOR_MAP if view_mode == "국가별" else REGION_COLOR_MAP

        if '매출월' in df_main.columns:
            m_df = df_main[df_main['매출월'] == sel_month]
            
            total_rev = m_df['매출액_숫자'].sum()
            curr_comm_df = df_comm[df_comm['매출월'] == sel_month] if not df_comm.empty else pd.DataFrame()
            comm_rev = curr_comm_df['매출액'].sum() if not curr_comm_df.empty else 0
            
            non_comm_rev = total_rev - comm_rev
            anpa_fee = total_rev * 0.20
            
            # --- 🚀 1. YTD (연누적) 계산 ---
            target_year_prefix = "20" + sel_month[:2] # 예: "2024"
            curr_month_order = all_dates_df[all_dates_df['매출월'] == sel_month]['월순서'].values[0]
            
            # 당해년도 YTD
            ytd_df = df_main[(df_main['월순서'].str.startswith(target_year_prefix)) & (df_main['월순서'] <= curr_month_order)]
            ytd_total = ytd_df['매출액_숫자'].sum()
            
            # 전년도 YTD (성장률 비교용)
            prev_year_prefix = str(int(target_year_prefix) - 1)
            prev_y_month_order = curr_month_order.replace(target_year_prefix, prev_year_prefix)
            pytd_df = df_main[(df_main['월순서'].str.startswith(prev_year_prefix)) & (df_main['월순서'] <= prev_y_month_order)]
            pytd_total = pytd_df['매출액_숫자'].sum()
            ytd_growth = (ytd_total - pytd_total) / pytd_total * 100 if pytd_total > 0 else 0
            # ---------------------------
            
            idx = month_list.index(sel_month)
            prev_total, prev_month, growth_rate = 0, "", 0
            prev_comm_rev, prev_non_comm_rev, prev_anpa_fee = 0, 0, 0
            comm_growth, non_comm_growth, anpa_growth = 0, 0, 0
            
            if idx < len(month_list) - 1:
                prev_month = month_list[idx + 1]
                prev_m_df = df_main[df_main['매출월'] == prev_month]
                prev_total = prev_m_df['매출액_숫자'].sum()
                
                prev_comm_df = df_comm[df_comm['매출월'] == prev_month] if not df_comm.empty else pd.DataFrame()
                prev_comm_rev = prev_comm_df['매출액'].sum() if not prev_comm_df.empty else 0
                
                prev_non_comm_rev = prev_total - prev_comm_rev
                prev_anpa_fee = prev_total * 0.20
                
                if prev_total > 0: growth_rate = (total_rev - prev_total) / prev_total * 100
                if prev_comm_rev > 0: comm_growth = (comm_rev - prev_comm_rev) / prev_comm_rev * 100
                if prev_non_comm_rev > 0: non_comm_growth = (non_comm_rev - prev_non_comm_rev) / prev_non_comm_rev * 100
                if prev_anpa_fee > 0: anpa_growth = (anpa_fee - prev_anpa_fee) / prev_anpa_fee * 100

            # 🔥 UI 카드 분할 표기 (YTD 포함)
            m1, m_ytd, m2, m3, m_space, m4 = st.columns([1, 1.2, 1, 1, 0.3, 1.2])
            
            with m1:
                if prev_total > 0: st.metric("총 매출액 (VAT 제외)", f"{total_rev:,.0f}원", f"{growth_rate:.1f}%")
                else: st.metric("총 매출액 (VAT 제외)", f"{total_rev:,.0f}원")
            with m_ytd:
                if pytd_total > 0: st.metric(f"📅 {target_year_prefix}년 누적(YTD)", f"{ytd_total:,.0f}원", f"{ytd_growth:+.1f}% (YoY)")
                else: st.metric(f"📅 {target_year_prefix}년 누적(YTD)", f"{ytd_total:,.0f}원")
            with m2:
                if prev_non_comm_rev > 0: st.metric("수수료 미지급 매출", f"{non_comm_rev:,.0f}원", f"{non_comm_growth:.1f}%")
                else: st.metric("수수료 미지급 매출", f"{non_comm_rev:,.0f}원")
            with m3:
                if prev_comm_rev > 0: st.metric("수수료 지급 매출", f"{comm_rev:,.0f}원", f"{comm_growth:.1f}%")
                else: st.metric("수수료 지급 매출", f"{comm_rev:,.0f}원")
                
            # 시각적 분리선 (회색 세로선) 추가
            with m_space:
                st.markdown("<div style='border-left: 2px solid #e0e0e0; height: 80px; margin: auto; width: 2px;'></div>", unsafe_allow_html=True)
                
            with m4:
                if prev_anpa_fee > 0: st.metric("💡 앤파 컨설팅수수료(20%)", f"{anpa_fee:,.0f}원", f"{anpa_growth:.1f}%")
                else: st.metric("💡 앤파 컨설팅수수료(20%)", f"{anpa_fee:,.0f}원")
                
            st.markdown("<br>", unsafe_allow_html=True)

            with st.container():
                st.markdown("### 💡 AI 자동 분석 리포트")
                if prev_total > 0:
                    diff_amt = total_rev - prev_total
                    if growth_rate > 0: st.success(f"📈 **전월 대비 총매출이 성장했습니다!** (+{diff_amt:,.0f}원 / +{growth_rate:.1f}%)")
                    elif growth_rate < 0: st.warning(f"📉 **전월 대비 총매출이 감소했습니다.** ({diff_amt:,.0f}원 / {growth_rate:.1f}%)")
                    if total_rev == df_main.groupby('매출월')['매출액_숫자'].sum().max(): st.info("🏆 **역대 최고 월 매출 기록!**")
                        
                    curr_nations = m_df.groupby('국적')['매출액_숫자'].sum()
                    prev_nations = prev_m_df.groupby('국적')['매출액_숫자'].sum()
                    growth_nations = curr_nations.subtract(prev_nations, fill_value=0)
                    
                    if not growth_nations.empty and growth_nations.max() > 0:
                        top_nation = growth_nations.idxmax()
                        top_growth_amt = growth_nations.max()
                        prev_amt = prev_nations.get(top_nation, 0)
                        rate_str = f" / +{(top_growth_amt / prev_amt * 100):.1f}%" if prev_amt > 0 else " / 순증가(신규)"
                        st.info(f"🔥 **가장 눈에 띄는 성장 국가:** **{top_nation}** (전월 대비 +{top_growth_amt:,.0f}원{rate_str})")
                else: st.info("비교 데이터 없음")
            st.divider()

            c1, c2 = st.columns([1, 1.2])
            with c1:
                n_df = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index()
                n_df = n_df[n_df['매출액_숫자'] > 0]
                
                pie_total = n_df['매출액_숫자'].sum()
                fig_pie = px.pie(n_df, values='매출액_숫자', names=group_col, hole=0.4, color=group_col, color_discrete_map=current_color_map)
                fig_pie.update_traces(textinfo='percent+label')
                fig_pie.update_layout(annotations=[dict(text=f"총 매출액<br><b>{pie_total:,.0f}원</b>", x=0.5, y=0.5, font_size=13, showarrow=False)])
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.subheader(f"📑 {view_mode} 상세 실적")
                st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>(단위: 원)</p>", unsafe_allow_html=True)
                
                def format_diff_func(row):
                    c, p, d = row['당월매출'], row['전월매출'], row['증감액']
                    if p == 0 and c > 0: return f"+{int(d):,} (순증가)"
                    if p == 0 and c == 0: return "-"
                    if d == 0: return "-"
                    rate = (d / p) * 100
                    sign = "+" if d > 0 else ""
                    icon = "🔺 " if d > 0 else "🔻 "
                    return f"{sign}{int(d):,} ({icon}{abs(rate):.1f}%)"

                curr_group = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index().rename(columns={'매출액_숫자': '당월매출'})
                if prev_total > 0:
                    prev_group = prev_m_df.groupby(group_col)['매출액_숫자'].sum().reset_index().rename(columns={'매출액_숫자': '전월매출'})
                    table_df = pd.merge(curr_group, prev_group, on=group_col, how='outer').fillna(0)
                else:
                    table_df = curr_group.copy()
                    table_df['전월매출'] = 0

                table_df['증감액'] = table_df['당월매출'] - table_df['전월매출']
                table_df = table_df.sort_values('당월매출', ascending=False)
                
                total_row = pd.DataFrame([{
                    group_col: '[ 총 합계 ]', '당월매출': table_df['당월매출'].sum(), 
                    '전월매출': table_df['전월매출'].sum(), '증감액': table_df['증감액'].sum()
                }])
                table_df = pd.concat([table_df, total_row], ignore_index=True)
                table_df[f'{sel_month}'] = table_df['당월매출'].apply(lambda x: f"{int(x):,}")
                
                if prev_total > 0:
                    table_df[f'{prev_month}(전월)'] = table_df['전월매출'].apply(lambda x: f"{int(x):,}")
                    table_df['전월대비'] = table_df.apply(format_diff_func, axis=1)
                    display_cols = [group_col, f'{prev_month}(전월)', f'{sel_month}', '전월대비']
                    col_config = {
                        f'{prev_month}(전월)': st.column_config.TextColumn(alignment="right"),
                        f'{sel_month}': st.column_config.TextColumn(alignment="right"),
                        '전월대비': st.column_config.TextColumn(alignment="right")
                    }
                else:
                    display_cols = [group_col, f'{sel_month}']
                    col_config = {f'{sel_month}': st.column_config.TextColumn(alignment="right")}

                st.dataframe(table_df[display_cols], use_container_width=True, hide_index=True, column_config=col_config)

            if view_mode == "권역별":
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("🔍 권역별 소속 국가 상세 (클릭하여 펼치기)")
                
                regions = [r for r in table_df[group_col].tolist() if r != '[ 총 합계 ]']
                
                for reg in regions:
                    with st.expander(f"📂 {reg} 소속 국가 상세 실적"):
                        reg_curr = m_df[m_df['권역'] == reg].groupby('국적')['매출액_숫자'].sum().reset_index().rename(columns={'매출액_숫자': '당월매출'})
                        
                        if prev_total > 0:
                            reg_prev = prev_m_df[prev_m_df['권역'] == reg].groupby('국적')['매출액_숫자'].sum().reset_index().rename(columns={'매출액_숫자': '전월매출'})
                            reg_table = pd.merge(reg_curr, reg_prev, on='국적', how='outer').fillna(0)
                        else:
                            reg_table = reg_curr.copy()
                            reg_table['전월매출'] = 0
                            
                        reg_table['증감액'] = reg_table['당월매출'] - reg_table['전월매출']
                        reg_table = reg_table.sort_values('당월매출', ascending=False)
                        
                        total_row_reg = pd.DataFrame([{
                            '국적': '[ 총 합계 ]', 
                            '당월매출': reg_table['당월매출'].sum(),
                            '전월매출': reg_table['전월매출'].sum(),
                            '증감액': reg_table['증감액'].sum()
                        }])
                        reg_table = pd.concat([reg_table, total_row_reg], ignore_index=True)
                        
                        reg_table[f'{sel_month}'] = reg_table['당월매출'].apply(lambda x: f"{int(x):,}")
                        
                        if prev_total > 0:
                            reg_table[f'{prev_month}(전월)'] = reg_table['전월매출'].apply(lambda x: f"{int(x):,}")
                            reg_table['전월대비'] = reg_table.apply(format_diff_func, axis=1)
                            
                            sub_cols = ['국적', f'{prev_month}(전월)', f'{sel_month}', '전월대비']
                            sub_config = {
                                f'{prev_month}(전월)': st.column_config.TextColumn(alignment="right"),
                                f'{sel_month}': st.column_config.TextColumn(alignment="right"),
                                '전월대비': st.column_config.TextColumn(alignment="right")
                            }
                        else:
                            sub_cols = ['국적', f'{sel_month}']
                            sub_config = {f'{sel_month}': st.column_config.TextColumn(alignment="right")}
                            
                        st.dataframe(reg_table[sub_cols], use_container_width=True, hide_index=True, column_config=sub_config)

            # 🔥 기간 필터가 적용된 월별 성장 추이
            st.divider()
            st.subheader(f"📈 전체 월별 성장 추이 ({view_mode} 기준)")
            
            # 여기서 슬라이더로 선택된 FILTERED_MONTHS 만 필터링
            filtered_main = df_main[df_main['매출월'].isin(FILTERED_MONTHS)]
            trend_df = filtered_main.groupby(['월순서', '매출월', group_col])['매출액_숫자'].sum().reset_index().sort_values('월순서')
            
            fig = go.Figure()
            for item in trend_df[group_col].unique():
                d = trend_df[trend_df[group_col] == item]
                fig.add_trace(go.Bar(x=d['매출월'], y=d['매출액_숫자'], name=item, text=item, textposition='auto', marker_color=current_color_map.get(item, '#cccccc')))
            
            # 🔥 Y축 M -> 백 단위 변경 및 스케일 자동 적용
            tot_series = filtered_main.groupby('매출월')['매출액_숫자'].sum().reindex(FILTERED_MONTHS).fillna(0)
            fig.add_trace(go.Scatter(x=tot_series.index, y=tot_series.values, name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}백" for v in tot_series.values], textposition="top center"))
            
            t_vals, t_txts = get_dynamic_ticks(tot_series.max())
            fig.update_layout(
                barmode='stack', hovermode="x unified", 
                xaxis={'categoryorder': 'array', 'categoryarray': FILTERED_MONTHS}, 
                yaxis=dict(tickmode='array', tickvals=t_vals, ticktext=t_txts),
                bargap=0.45
            )
            st.plotly_chart(fig, use_container_width=True)

    # ==========================================================
    # --- 메뉴 2: 수수료 매출 (에이전트별) ---
    # ==========================================================
    else:
        agent_options = ["전체"] + sorted(df_comm['에이전트'].dropna().unique().tolist())
        sel_agent = st.sidebar.selectbox("🧑‍💼 에이전트 상세 필터", agent_options)

        if sel_agent == "전체":
            page_df = df_comm.copy()
            g_col = '에이전트'
            page_title = "수수료 매출 전체 분석"
        else:
            page_df = df_comm[df_comm['에이전트'] == sel_agent].copy()
            g_col = '국적'
            page_title = f"[{sel_agent}] 에이전트 상세 분석"

        st.title(f"💸 {sel_month} {page_title}")
        
        if not page_df.empty:
            curr_comm = page_df[page_df['매출월'] == sel_month]
            
            # 🔥 기본 지표 및 수수료 계산
            total_comm_rev = curr_comm['매출액'].sum()
            c_paid_comm = curr_comm['지급수수료'].sum()
            c_net_rev = curr_comm['실매출액'].sum()
            
            idx = month_list.index(sel_month)
            p_comm_total, p_paid_comm, p_net_rev, p_month = 0, 0, 0, ""
            c_growth_rate, paid_growth_rate, net_growth_rate = 0, 0, 0
            
            if idx < len(month_list) - 1:
                p_month = month_list[idx + 1]
                p_comm_df = page_df[page_df['매출월'] == p_month]
                p_comm_total = p_comm_df['매출액'].sum()
                p_paid_comm = p_comm_df['지급수수료'].sum()
                p_net_rev = p_comm_df['실매출액'].sum()
                
                if p_comm_total > 0: c_growth_rate = (total_comm_rev - p_comm_total) / p_comm_total * 100
                if p_paid_comm > 0: paid_growth_rate = (c_paid_comm - p_paid_comm) / p_paid_comm * 100
                if p_net_rev > 0: net_growth_rate = (c_net_rev - p_net_rev) / p_net_rev * 100

            # 🔥 UI 카드 3개 분할 표기 (총수납액, 지급수수료, 실매출액)
            m1, m2, m3 = st.columns(3)
            metric_title = "총 수납액 합계" if sel_agent == "전체" else f"[{sel_agent}] 총 수납액"
            
            with m1:
                if p_comm_total > 0: st.metric(metric_title, f"{total_comm_rev:,.0f}원", f"{c_growth_rate:.1f}%")
                else: st.metric(metric_title, f"{total_comm_rev:,.0f}원")
            with m2:
                if p_paid_comm > 0: st.metric("지급수수료", f"{c_paid_comm:,.0f}원", f"{paid_growth_rate:.1f}%")
                else: st.metric("지급수수료", f"{c_paid_comm:,.0f}원")
            with m3:
                if p_net_rev > 0: st.metric("실매출액(총수납액-지급수수료)", f"{c_net_rev:,.0f}원", f"{net_growth_rate:.1f}%")
                else: st.metric("실매출액(총수납액-지급수수료)", f"{c_net_rev:,.0f}원")

            with st.container():
                st.markdown(f"### 💡 AI 실적 분석 리포트")
                if p_comm_total > 0:
                    c_diff_amt = total_comm_rev - p_comm_total
                    if c_growth_rate > 0: st.success(f"📈 **전월 대비 매출액이 증가했습니다!** (+{c_diff_amt:,.0f}원 / +{c_growth_rate:.1f}%)")
                    elif c_growth_rate < 0: st.warning(f"📉 **전월 대비 매출액이 감소했습니다.** ({c_diff_amt:,.0f}원 / {c_growth_rate:.1f}%)")
                    
                    if total_comm_rev == page_df.groupby('매출월')['매출액'].sum().max() and total_comm_rev > 0: 
                        st.info(f"🏆 **역대 최고치 경신!**")
                    
                    c_groups = curr_comm.groupby(g_col)['매출액'].sum()
                    p_groups = p_comm_df.groupby(g_col)['매출액'].sum()
                    group_diff = c_groups.subtract(p_groups, fill_value=0)
                    
                    label_name = "에이전트" if sel_agent == "전체" else "국가"
                    
                    if not group_diff.empty:
                        top_g = group_diff.idxmax()
                        top_diff_amt = group_diff.max()
                        bottom_g = group_diff.idxmin()
                        bottom_diff_amt = group_diff.min()

                        if top_diff_amt > 0:
                            p_g_amt = p_groups.get(top_g, 0)
                            a_rate_str = f" / +{(top_diff_amt / p_g_amt * 100):.1f}%" if p_g_amt > 0 else " / 순증가(신규)"
                            st.info(f"🚀 **최대 성장 {label_name}:** **{top_g}** (전월 대비 +{top_diff_amt:,.0f}원{a_rate_str})")
                            
                        if bottom_diff_amt < 0:
                            p_g_amt_bottom = p_groups.get(bottom_g, 0)
                            b_rate_str = f" / {(bottom_diff_amt / p_g_amt_bottom * 100):.1f}%" if p_g_amt_bottom > 0 else ""
                            st.error(f"🔻 **최대 감소 {label_name}:** **{bottom_g}** (전월 대비 {bottom_diff_amt:,.0f}원{b_rate_str})")
                else: st.info("비교 데이터가 부족하여 분석을 생략합니다.")
            st.divider()

            if sel_agent == "전체":
                st.subheader(f"🗺️ {sel_month} 에이전트별 국가 구성비")
                if not curr_comm.empty:
                    comp = curr_comm.groupby(['에이전트', '국적'])['매출액'].sum().reset_index()
                    comp = comp[comp['매출액'] > 0]
                    
                    # 🔥 X축 스케일 M -> 백 단위 자동 변경 적용
                    fig_comp_bar = px.bar(comp, x='매출액', y='에이전트', color='국적', orientation='h', text='국적', color_discrete_map=NATION_COLOR_MAP)
                    fig_comp_bar.update_traces(textposition='inside')
                    
                    bar_max = comp.groupby('에이전트')['매출액'].sum().max() if not comp.empty else 0
                    b_vals, b_txts = get_dynamic_ticks(bar_max)
                    
                    fig_comp_bar.update_layout(
                        barmode='stack', 
                        height=400,
                        xaxis=dict(tickmode='array', tickvals=b_vals, ticktext=b_txts)
                    )
                    st.plotly_chart(fig_comp_bar, use_container_width=True)
                    
                    st.subheader("📑 상세 정산 내역")
                    st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>(단위: 원)</p>", unsafe_allow_html=True)
                    
                    curr_group = curr_comm.groupby(['에이전트'])['매출액'].sum().reset_index().rename(columns={'매출액': '당월매출'})
                    
                    if p_comm_total > 0:
                        prev_group = p_comm_df.groupby(['에이전트'])['매출액'].sum().reset_index().rename(columns={'매출액': '전월매출'})
                        table_comm = pd.merge(curr_group, prev_group, on=['에이전트'], how='outer').fillna(0)
                    else:
                        table_comm = curr_group.copy()
                        table_comm['전월매출'] = 0

                    table_comm['증감액'] = table_comm['당월매출'] - table_comm['전월매출']
                    table_comm = table_comm.sort_values('당월매출', ascending=False)
                    
                    # 🔥 에이전트 컬럼명 변경 및 수수료율 표기
                    table_comm['에이전트(수수료율)'] = table_comm['에이전트'].apply(lambda x: f"{x}({int(COMMISSION_RATES.get(x, 0.15)*100)}%)")
                    
                    total_row_comm = pd.DataFrame([{
                        '에이전트(수수료율)': '[ 총 합계 ]', 
                        '당월매출': table_comm['당월매출'].sum(),
                        '전월매출': table_comm['전월매출'].sum(),
                        '증감액': table_comm['증감액'].sum()
                    }])
                    table_comm = pd.concat([table_comm, total_row_comm], ignore_index=True)
                    
                    table_comm[f'{sel_month}'] = table_comm['당월매출'].apply(lambda x: f"{int(x):,}")
                    
                    if p_comm_total > 0:
                        table_comm[f'{p_month}(전월)'] = table_comm['전월매출'].apply(lambda x: f"{int(x):,}")
                        def format_diff(row):
                            c, p, d = row['당월매출'], row['전월매출'], row['증감액']
                            if p == 0 and c > 0: return f"+{int(d):,} (순증가)"
                            if p == 0 and c == 0: return "-"
                            if d == 0: return "-"
                            rate = (d / p) * 100
                            sign = "+" if d > 0 else ""
                            icon = "🔺 " if d > 0 else "🔻 "
                            return f"{sign}{int(d):,} ({icon}{abs(rate):.1f}%)"
                            
                        table_comm['전월대비'] = table_comm.apply(format_diff, axis=1)
                        display_cols = ['에이전트(수수료율)', f'{p_month}(전월)', f'{sel_month}', '전월대비']
                        col_config = {
                            f'{p_month}(전월)': st.column_config.TextColumn(alignment="right"),
                            f'{sel_month}': st.column_config.TextColumn(alignment="right"),
                            '전월대비': st.column_config.TextColumn(alignment="right")
                        }
                    else:
                        display_cols = ['에이전트(수수료율)', f'{sel_month}']
                        col_config = {f'{sel_month}': st.column_config.TextColumn(alignment="right")}
                        
                    st.dataframe(table_comm[display_cols], use_container_width=True, hide_index=True, column_config=col_config)
            else:
                st.subheader(f"🗺️ {sel_month} [{sel_agent}] 소속 국가 구성비")
                if not curr_comm.empty:
                    col1, col2 = st.columns([1, 1.2])
                    
                    with col1:
                        comp = curr_comm.groupby(['국적'])['매출액'].sum().reset_index()
                        comp = comp[comp['매출액'] > 0]
                        
                        comp_total = comp['매출액'].sum()
                        fig_comp = px.pie(comp, values='매출액', names='국적', hole=0.4, color='국적', color_discrete_map=NATION_COLOR_MAP)
                        fig_comp.update_traces(textinfo='percent+label')
                        fig_comp.update_layout(annotations=[dict(text=f"총 수납액<br><b>{comp_total:,.0f}원</b>", x=0.5, y=0.5, font_size=13, showarrow=False)])
                        st.plotly_chart(fig_comp, use_container_width=True)
                        
                    with col2:
                        st.subheader("📑 상세 정산 내역")
                        st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>(단위: 원)</p>", unsafe_allow_html=True)
                        
                        curr_group = curr_comm.groupby(['국적'])['매출액'].sum().reset_index().rename(columns={'매출액': '당월매출'})
                        
                        if p_comm_total > 0:
                            prev_group = p_comm_df.groupby(['국적'])['매출액'].sum().reset_index().rename(columns={'매출액': '전월매출'})
                            table_comm = pd.merge(curr_group, prev_group, on=['국적'], how='outer').fillna(0)
                        else:
                            table_comm = curr_group.copy()
                            table_comm['전월매출'] = 0

                        table_comm['증감액'] = table_comm['당월매출'] - table_comm['전월매출']
                        table_comm = table_comm.sort_values('당월매출', ascending=False)
                        
                        total_row_comm = pd.DataFrame([{
                            '국적': '[ 총 합계 ]', 
                            '당월매출': table_comm['당월매출'].sum(),
                            '전월매출': table_comm['전월매출'].sum(),
                            '증감액': table_comm['증감액'].sum()
                        }])
                        table_comm = pd.concat([table_comm, total_row_comm], ignore_index=True)
                        
                        table_comm[f'{sel_month}'] = table_comm['당월매출'].apply(lambda x: f"{int(x):,}")
                        
                        if p_comm_total > 0:
                            table_comm[f'{p_month}(전월)'] = table_comm['전월매출'].apply(lambda x: f"{int(x):,}")
                            def format_diff(row):
                                c, p, d = row['당월매출'], row['전월매출'], row['증감액']
                                if p == 0 and c > 0: return f"+{int(d):,} (순증가)"
                                if p == 0 and c == 0: return "-"
                                if d == 0: return "-"
                                rate = (d / p) * 100
                                sign = "+" if d > 0 else ""
                                icon = "🔺 " if d > 0 else "🔻 "
                                return f"{sign}{int(d):,} ({icon}{abs(rate):.1f}%)"
                                
                            table_comm['전월대비'] = table_comm.apply(format_diff, axis=1)
                            display_cols = ['국적', f'{p_month}(전월)', f'{sel_month}', '전월대비']
                            col_config = {
                                f'{p_month}(전월)': st.column_config.TextColumn(alignment="right"),
                                f'{sel_month}': st.column_config.TextColumn(alignment="right"),
                                '전월대비': st.column_config.TextColumn(alignment="right")
                            }
                        else:
                            display_cols = ['국적', f'{sel_month}']
                            col_config = {f'{sel_month}': st.column_config.TextColumn(alignment="right")}
                            
                        st.dataframe(table_comm[display_cols], use_container_width=True, hide_index=True, column_config=col_config)

            # 🔥 기간 필터가 적용된 수수료 매출 추이
            st.divider()
            chart_subtitle = "에이전트별 누적" if sel_agent == "전체" else "국가(국적)별 누적"
            st.subheader(f"📈 월별 수수료 매출 추이 ({chart_subtitle})")
            
            # 여기서 슬라이더로 선택된 FILTERED_MONTHS 만 필터링
            filtered_page = page_df[page_df['매출월'].isin(FILTERED_MONTHS)]
            trend_data = filtered_page.groupby(['월순서', '매출월', g_col])['매출액'].sum().reset_index().sort_values('월순서')
            
            fig_ctrend = go.Figure()
            for g_item in trend_data[g_col].unique():
                a_data = trend_data[trend_data[g_col] == g_item]
                c_color = AGENT_COLOR_MAP.get(g_item, '#ccc') if sel_agent == "전체" else NATION_COLOR_MAP.get(g_item, '#ccc')
                fig_ctrend.add_trace(go.Bar(x=a_data['매출월'], y=a_data['매출액'], name=g_item, text=g_item, textposition='auto', marker_color=c_color))
            
            total_cline_series = filtered_page.groupby('매출월')['매출액'].sum().reindex(FILTERED_MONTHS).fillna(0)
            fig_ctrend.add_trace(go.Scatter(x=total_cline_series.index, y=total_cline_series.values, name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}백" for v in total_cline_series.values], textposition="top center"))
            
            # 🔥 Y축 스케일 자동 적용
            c_vals, c_txts = get_dynamic_ticks(total_cline_series.max())
            fig_ctrend.update_layout(
                barmode='stack', hovermode="x unified", height=500, 
                xaxis={'categoryorder': 'array', 'categoryarray': FILTERED_MONTHS}, 
                yaxis=dict(tickmode='array', tickvals=c_vals, ticktext=c_txts),
                bargap=0.45
            )
            st.plotly_chart(fig_ctrend, use_container_width=True)
