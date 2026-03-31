import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="온리프 해외매출 대시보드", layout="wide")

file_name = "온리프 해외매출.csv"

# 고정 에이전트 리스트
FIXED_AGENTS = ["천수현", "The SC", "레이블", "앤티스"]

# 권역별 고정 색상
color_map = {
    "중화권": "#000080", "일본": "#006400", "북미": "#E1AD01",
    "동남아": "#FF4B4B", "유럽": "#7D3C98", "남미": "#FF8C00", 
    "중동": "#8B4513", "기타": "#A9DFBF"
}

def to_n(v):
    """숫자 데이터 정제"""
    if pd.isna(v) or str(v).strip() == "": return 0
    s = str(v).replace(',', '').replace(' ', '').replace('"', '').replace('원', '').replace('△', '-')
    try: return float(s)
    except: return 0

try:
    # 2. 데이터 로드
    raw_df = pd.read_csv(file_name, header=None, encoding='utf-8-sig')
    
    # 3. 월 정보 추출
    months_raw = [str(m).strip() for m in raw_df.iloc[1, 3:9].values]
    months_disp = [f"{m[2:4]}년 {m[4:6]}월" for m in months_raw]

    # --- 사이드바 메뉴 및 공통 필터 설정 ---
    st.sidebar.title("📊 메뉴 이동")
    page = st.sidebar.radio("원하시는 리포트를 선택하세요:", 
                            ["🌐 전체 매출 요약 (원형 그래프)", "🤝 수수료 매출 (월별/경로별 상세)"])
    st.sidebar.write("---")
    
    sel_month = st.sidebar.selectbox("📅 조회할 월을 선택하세요", months_disp, index=len(months_disp)-1)

    # ==========================================
    # 첫 번째 페이지: 전체 매출 요약
    # ==========================================
    if page == "🌐 전체 매출 요약 (원형 그래프)":
        st.title("📊 온리프 해외매출 권역별 비중 분석")
        start_row = 0
        for i in range(len(raw_df)):
            if str(raw_df.iloc[i, 1]).strip() == "중화권":
                start_row = i
                break
        target_regions = ["중화권", "일본", "북미", "동남아", "유럽", "남미", "중동", "기타"]
        summary_data = []
        if start_row > 0:
            for i in range(start_row, min(start_row + 15, len(raw_df))):
                region_name = str(raw_df.iloc[i, 1]).strip()
                if region_name in target_regions:
                    for idx, m_name in enumerate(months_disp):
                        summary_data.append({"월": m_name, "권역": region_name, "매출액": to_n(raw_df.iloc[i, 3 + idx])})
        df_summary = pd.DataFrame(summary_data)
        df_selected = df_summary[df_summary['월'] == sel_month].copy()
        total_val = df_selected['매출액'].sum()

        col_m1, col_m2 = st.columns(2)
        with col_m1: st.metric(f"📍 {sel_month} 해외매출 총합", f"{total_val:,.0f}원")
        
        st.write("---")
        c1, c2 = st.columns([1.3, 1])
        with c1:
            fig_pie = px.pie(df_selected, values='매출액', names='권역', color='권역', color_discrete_map=color_map, hole=0.4)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            st.subheader("📊 권역별 상세 실적")
            df_table = df_selected.sort_values('매출액', ascending=False).reset_index(drop=True)
            df_table.index = df_table.index + 1
            if total_val > 0: df_table['비중'] = (df_table['매출액'] / total_val * 100).round(1).astype(str) + '%'
            else: df_table['비중'] = '0%'
            sum_row = pd.DataFrame({'권역': ['[ 월 합계 ]'], '매출액': [total_val], '비중': ['100.0%']}, index=['Σ'])
            st.table(pd.concat([df_table[['권역', '매출액', '비중']], sum_row]).style.format({'매출액': '{:,.0f}'}))

        st.write("---")
        st.subheader("📈 전체 해외매출 월별 성장 추이 (권역별 구성)")
        trend_total = df_summary.groupby("월")["매출액"].sum().reset_index()
        fig_trend_comb = px.bar(df_summary, x="월", y="매출액", color="권역", text="권역", color_discrete_map=color_map, category_orders={"월": months_disp})
        
        # ✨ 막대 폭 조정 (70%)
        fig_trend_comb.update_traces(width=0.7, textposition='inside', insidetextanchor='middle', selector=dict(type='bar'))
        
        fig_trend_comb.add_scatter(x=trend_total["월"], y=trend_total["매출액"], mode="lines+markers+text", name="해외매출 총합",
                                   line=dict(color="black", width=3), text=[f"{v/1e6:.1f}M" for v in trend_total["매출액"]], textposition="top center")
        st.plotly_chart(fig_trend_comb, use_container_width=True)

    # ==========================================
    # 두 번째 페이지: 수수료 매출 상세
    # ==========================================
    elif page == "🤝 수수료 매출 (월별/경로별 상세)":
        st.title("🤝 수수료 매출 (에이전트 유입) 상세 분석")
        
        comm_data = []
        current_path = "기타"
        
        for i in range(2, 50):
            col0_val = str(raw_df.iloc[i, 0]).strip()
            col1_val = str(raw_df.iloc[i, 1]).strip()
            if "비수수료" in col0_val or "비수수료" in col1_val: break
            if col1_val not in ["nan", "", "소계", "총합계", "구분"]: current_path = col1_val
            country = str(raw_df.iloc[i, 2]).strip()
            if country in ["nan", "", "소계", "총합계", "구분"]: continue
            for idx, m_name in enumerate(months_disp):
                val = to_n(raw_df.iloc[i, 3 + idx])
                comm_data.append({"월": m_name, "유입경로": current_path, "국가": country, "매출액": val})

        df_comm = pd.DataFrame(comm_data)

        if df_comm.empty:
            st.warning("데이터가 비어있습니다.")
        else:
            all_possible_agents = sorted(list(set(df_comm['유입경로'].unique()) | set(FIXED_AGENTS)))
            agent_colors = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel
            agent_color_map = {agent: agent_colors[i % len(agent_colors)] for i, agent in enumerate(all_possible_agents)}
            unique_countries = sorted(df_comm['국가'].unique())
            country_color_map = {c: (px.colors.qualitative.Alphabet + px.colors.qualitative.Vivid)[i % 40] for i, c in enumerate(unique_countries)}

            st.subheader("📈 월별 수수료 매출 전체 추이")
            path_trend = df_comm.groupby(["월", "유입경로"])["매출액"].sum().reset_index()
            comm_trend = df_comm.groupby("월")["매출액"].sum().reset_index()

            fig_combined = px.bar(path_trend[path_trend['매출액']>0], x="월", y="매출액", color="유입경로", text="유입경로", color_discrete_map=agent_color_map)
            
            # ✨ 막대 폭 조정 (70%)
            fig_combined.update_traces(width=0.7, textposition='inside', insidetextanchor='middle', selector=dict(type='bar'))
            
            fig_combined.add_scatter(x=comm_trend["월"], y=comm_trend["매출액"], mode="lines+markers+text", name="총합",
                                     line=dict(color="black", width=3), text=[f"{v/1e6:.1f}M" for v in comm_trend["매출액"]], textposition="top center")
            st.plotly_chart(fig_combined, use_container_width=True)

            st.write("---")
            st.subheader(f"🌐 {sel_month} 에이전트별 국가 구성비")
            df_comm_sel = df_comm[df_comm['월'] == sel_month]
            
            agent_totals = df_comm_sel.groupby("유입경로")["매출액"].sum().reset_index()
            for fa in FIXED_AGENTS:
                if fa not in agent_totals['유입경로'].values:
                    agent_totals = pd.concat([agent_totals, pd.DataFrame({'유입경로': [fa], '매출액': [0]})])
            
            agent_totals = agent_totals.sort_values("매출액", ascending=False).reset_index(drop=True)
            sorted_agents = agent_totals["유입경로"].tolist()
            
            comp_df = df_comm_sel[df_comm_sel['매출액']>0].groupby(["유입경로", "국가"])["매출액"].sum().reset_index()
            
            fig_comp = px.bar(comp_df, x="매출액", y="유입경로", color="국가", orientation='h', text="국가", 
                              category_orders={"유입경로": sorted_agents[::-1]}, color_discrete_map=country_color_map)
            
            # ✨ 가로형 막대 폭 조정 (70%)
            fig_comp.update_traces(width=0.7, textposition='inside', insidetextanchor='middle')
            
            fig_comp.update_xaxes(dtick=5000000, showgrid=True, gridcolor='LightGray', gridwidth=1, tickformat=",d")
            fig_comp.update_layout(height=450, xaxis_title="매출액 (원)", yaxis_title="")
            st.plotly_chart(fig_comp, use_container_width=True)

            st.write("---")
            col1, col2 = st.columns([1, 2.5])
            with col1:
                st.markdown(f"#### 🏆 {sel_month} 에이전트 실적 순위")
                agent_rank = agent_totals.copy()
                agent_rank.index = agent_rank.index + 1
                sum_agent = pd.DataFrame({'유입경로': ['[ 총 합계 ]'], '매출액': [agent_rank['매출액'].sum()]}, index=['Σ'])
                st.dataframe(pd.concat([agent_rank, sum_agent]).style.format({'매출액': '{:,.0f}'}), use_container_width=True)

            with col2:
                st.markdown("#### 📋 전체 기간 상세 표")
                pivot_comm = df_comm.pivot_table(index=["유입경로", "국가"], columns="월", values="매출액", aggfunc="sum", fill_value=0)
                pivot_comm['총계'] = pivot_comm.sum(axis=1)
                st.dataframe(pivot_comm.sort_values('총계', ascending=False).style.format("{:,.0f}"), use_container_width=True)

except Exception as e:
    st.error(f"오류 발생: {e}")