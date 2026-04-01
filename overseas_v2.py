import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외매출 실시간 대시보드", layout="wide")

# ⚠️ 여기에 새로 복사한 '웹에 게시' CSV 주소를 붙여넣으세요.
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS..." 

# 디자인 테마 (권역별 색상)
COLOR_MAP = {
    "중화권": "#000080", "북미": "#E1AD01", "일본": "#006400",
    "동남아": "#FF4B4B", "남미": "#FF8C00", "유럽": "#7D3C98", 
    "기타": "#A9DFBF", "중동": "#8B4513"
}

def clean_numeric(v):
    """문자열 숫자를 깨끗한 숫자로 변환 (₩, 쉼표 제거)"""
    if pd.isna(v): return 0
    s = str(v).replace('₩', '').replace(',', '').replace(' ', '').replace('△', '-').strip()
    try: return float(s)
    except: return 0

@st.cache_data(ttl=30) # 30초마다 데이터 갱신
def get_data(url):
    try:
        res = requests.get(url)
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None

# 데이터 불러오기
raw_df = get_data(CSV_URL)

if raw_df is not None:
    try:
        # --- 데이터 파싱 (시트 구조 자동 탐색) ---
        # 1. 월 목록 찾기 (26년 01월 등이 적힌 행 찾기)
        month_row_idx = 1 # 보통 2행에 위치
        months_raw = [str(m).strip() for m in raw_df.iloc[month_row_idx, 3:15].values if str(m) != 'nan']
        months_disp = [f"{m[2:4]}년 {m[4:6]}월" for m in months_raw]

        # 2. 권역 데이터 시작 행 찾기
        start_row = 0
        for i in range(len(raw_df)):
            if "중화권" in str(raw_df.iloc[i, 1]):
                start_row = i
                break

        # 3. 데이터 정리
        target_regions = ["중화권", "북미", "일본", "동남아", "남미", "유럽", "기타", "중동"]
        all_data = []
        if start_row > 0:
            for i in range(start_row, start_row + 15): # 15개 행 안에서 검색
                region = str(raw_df.iloc[i, 1]).strip()
                if region in target_regions:
                    for idx, m_name in enumerate(months_disp):
                        val = clean_numeric(raw_df.iloc[i, 3 + idx])
                        all_data.append({"월": m_name, "권역": region, "매출액": val})
        
        final_df = pd.DataFrame(all_data)

        # --- 대시보드 화면 구성 ---
        st.sidebar.title("🗓️ 기간 선택")
        selected_month = st.sidebar.selectbox("조회할 월을 선택하세요", months_disp, index=len(months_disp)-1)

        st.title(f"📊 온리프 해외매출 권역별 비중 분석")
        st.caption(f"📍 {selected_month} 해외매출 종합")

        # 상단 지표 (Metric)
        curr_month_df = final_df[final_df['월'] == selected_month]
        total_sales = curr_month_df['매출액'].sum()
        
        st.header(f"{total_sales:,.0f}원")
        st.divider()

        col1, col2 = st.columns([1.2, 1])

        with col1:
            # 원형 차트
            fig_pie = px.pie(curr_month_df, values='매출액', names='권역', 
                             color='권역', color_discrete_map=COLOR_MAP,
                             hole=0.4)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # 상세 수치 표
            st.subheader("📑 권역별 상세 실적")
            table_df = curr_month_df.sort_values('매출액', ascending=False).reset_index(drop=True)
            table_df.index += 1
            # 합계 및 비중 계산
            table_df['비중'] = (table_df['매출액'] / total_sales * 100).map('{:.1f}%'.format)
            
            # 합계 행 추가
            sum_df = pd.DataFrame([{"권역": "[ 월 합계 ]", "매출액": total_sales, "비중": "100.0%"}], index=["Σ"])
            st.table(pd.concat([table_df[['권역', '매출액', '비중']], sum_df]))

        # 하단 트렌드 차트
        st.divider()
        st.subheader("📈 전체 해외매출 월별 성장 추이 (권역별 구성)")
        fig_trend = px.bar(final_df, x="월", y="매출액", color="권역", 
                           color_discrete_map=COLOR_MAP,
                           category_orders={"월": months_disp})
        st.plotly_chart(fig_trend, use_container_width=True)

    except Exception as e:
        st.error(f"코드 실행 중 오류가 발생했습니다: {e}")
else:
    st.info("구글 시트에서 데이터를 불러오고 있습니다. 잠시만 기다려주세요.")
