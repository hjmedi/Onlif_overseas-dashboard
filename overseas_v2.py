import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# ─────────────────────────────────────────────
# 1. 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="온리프 해외 매출 통합 관리",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# 2. 커스텀 CSS (디자인 개선)
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* 전체 폰트 & 배경 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: linear-gradient(160deg, #1a1f36 0%, #0d1117 100%);
    }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stRadio > label { color: #94a3b8 !important; font-size: 0.85rem; }

    /* 메트릭 카드 */
    [data-testid="metric-container"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    [data-testid="metric-container"]:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] { font-size: 0.75rem; color: #64748b; font-weight: 500; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 1.4rem; font-weight: 700; color: #1e293b; }

    /* 타이틀 */
    h1 { color: #1e293b; font-weight: 700; letter-spacing: -0.5px; }
    h2, h3 { color: #334155; font-weight: 600; }

    /* 구분선 */
    hr { border-color: #e2e8f0; margin: 1.5rem 0; }

    /* 성공/경고/정보 박스 */
    .stSuccess, .stWarning, .stInfo, .stError {
        border-radius: 10px;
        font-size: 0.9rem;
    }

    /* 데이터프레임 헤더 */
    [data-testid="stDataFrame"] th {
        background-color: #1e293b !important;
        color: white !important;
        font-weight: 600;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        color: #3b82f6 !important;
        border-bottom: 2px solid #3b82f6;
    }

    /* 로딩 스피너 */
    .loading-text {
        color: #64748b;
        font-size: 0.9rem;
        text-align: center;
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 3. 설정 상수
# ─────────────────────────────────────────────
URL_MAIN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"

COMMISSION_URLS = {
    "레이블":     "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1298456060&single=true&output=csv",
    "The SC":     "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=344598450&single=true&output=csv",
    "천수현 대표": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1973655230&single=true&output=csv",
    "앤티스":     "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2053307016&single=true&output=csv",
    "크리에이트립": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2000088021&single=true&output=csv",
}

COMMISSION_RATES = {
    "레이블": 0.15,
    "The SC": 0.15,
    "천수현 대표": 0.15,
    "앤티스": 0.15,
    "크리에이트립": 0.11,
}

ANPA_FEE_RATE = 0.20


# ─────────────────────────────────────────────
# 4. 순수 유틸 함수
# ─────────────────────────────────────────────
def get_region(nation: str) -> str:
    nation = str(nation).strip()
    mapping = {
        "중화권": ["중국", "대만", "홍콩", "마카오", "China", "Taiwan", "Hong Kong"],
        "일본":   ["일본", "Japan"],
        "동남아": ["태국", "베트남", "싱가포르", "필리핀", "말레이시아", "인도네시아", "미얀마", "캄보디아", "라오스"],
        "북미":   ["미국", "캐나다", "USA", "Canada", "United States"],
        "유럽":   ["영국", "프랑스", "독일", "이탈리아", "스페인", "러시아", "네덜란드"],
    }
    for region, nations in mapping.items():
        if nation in nations:
            return region
    return "기타"


def to_numeric(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).replace("₩", "").replace(",", "").replace(" ", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def get_dynamic_ticks(max_val):
    """Y축 눈금값과 텍스트를 동적으로 생성 (만/억 단위)"""
    if pd.isna(max_val) or max_val == 0:
        return [0], ["0"]
    if max_val >= 100_000_000:
        step = 50_000_000
    elif max_val >= 50_000_000:
        step = 20_000_000
    elif max_val >= 20_000_000:
        step = 10_000_000
    elif max_val >= 10_000_000:
        step = 5_000_000
    else:
        step = 2_000_000

    vals = list(range(0, int(max_val) + step * 2, step))
    txts = []
    for v in vals:
        if v == 0:
            txts.append("0")
        elif v >= 100_000_000:
            txts.append(f"{v / 100_000_000:g}억")
        elif v >= 10_000:
            txts.append(f"{v / 10_000:g}만")
        else:
            txts.append(f"{v:,}")
    return vals, txts


def format_amount(v: float) -> str:
    """금액을 만/억 단위 축약 텍스트로 변환"""
    if v >= 100_000_000:
        return f"{v / 100_000_000:.1f}억"
    elif v >= 10_000:
        return f"{v / 10_000:.0f}만"
    return f"{v:,.0f}"


def format_diff(curr: float, prev: float) -> str:
    """전월 대비 증감 텍스트 생성 (공통 함수)"""
    d = curr - prev
    if prev == 0 and curr > 0:
        return f"+{int(d):,} (순증가)"
    if prev == 0 and curr == 0:
        return "-"
    if d == 0:
        return "-"
    rate = (d / prev) * 100
    sign = "+" if d > 0 else ""
    icon = "🔺 " if d > 0 else "🔻 "
    return f"{sign}{int(d):,} ({icon}{abs(rate):.1f}%)"


# ─────────────────────────────────────────────
# 5. 데이터 로딩
# ─────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_all_data():
    errors = []

    # ── 메인 데이터 ──
    try:
        res_m = requests.get(URL_MAIN, timeout=10)
        res_m.raise_for_status()
        df_m_raw = pd.read_csv(StringIO(res_m.content.decode("utf-8-sig")), header=None)

        h_idx = 0
        for i in range(len(df_m_raw)):
            if "이름" in "".join(df_m_raw.iloc[i].fillna("").astype(str)):
                h_idx = i
                break

        df_m = df_m_raw.copy()
        df_m.columns = [str(c).strip() for c in df_m.iloc[h_idx].fillna("미지정")]
        df_m = df_m.iloc[h_idx + 1:].reset_index(drop=True)

        div_col = [c for c in df_m.columns if "구분" in c or "해외" in c]
        if div_col:
            df_m = df_m[df_m[div_col[0]].astype(str).str.contains("해외", na=False)]

        amt_col = [c for c in df_m.columns if "수납액" in c and "CRM" in c]
        if not amt_col:
            amt_col = [c for c in df_m.columns if "수납액" in c]

        df_m["매출액_숫자"] = df_m[amt_col[0]].apply(to_numeric) / 1.1 if amt_col else 0
        df_m["권역"] = df_m["국적"].apply(get_region)
    except Exception as e:
        errors.append(f"메인 데이터 로딩 실패: {e}")
        df_m = pd.DataFrame()

    # ── 에이전트 수수료 데이터 ──
    comm_list = []
    for name, url in COMMISSION_URLS.items():
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            temp = pd.read_csv(StringIO(r.content.decode("utf-8-sig")))
            df_c = pd.DataFrame({
                "에이전트": name,
                "국적":     temp.iloc[:, 3],
                "날짜":     temp.iloc[:, 4],
                "매출액":   temp.iloc[:, 8].apply(to_numeric),
            })
            if name == "크리에이트립":
                df_c = df_c[df_c["국적"].astype(str).str.contains("중국", na=False)]
            comm_list.append(df_c)
        except Exception as e:
            errors.append(f"[{name}] 데이터 로딩 실패: {e}")

    df_comm = pd.concat(comm_list, ignore_index=True) if comm_list else pd.DataFrame()

    if not df_comm.empty:
        df_comm["수수료율"]  = df_comm["에이전트"].map(COMMISSION_RATES).fillna(0.15)
        df_comm["지급수수료"] = df_comm["매출액"] * df_comm["수수료율"]
        df_comm["실매출액"]  = df_comm["매출액"] - df_comm["지급수수료"]

    return df_m, df_comm, errors


def add_date_columns(df: pd.DataFrame, col_keyword: str) -> pd.DataFrame:
    target = [c for c in df.columns if col_keyword in c]
    if target:
        df["날짜형"] = pd.to_datetime(df[target[0]], errors="coerce")
        df = df.dropna(subset=["날짜형"])
        df["매출월"] = df["날짜형"].dt.strftime("%y년 %m월")
        df["월순서"] = df["날짜형"].dt.strftime("%Y-%m")
    return df


# ─────────────────────────────────────────────
# 6. 색상 맵 생성
# ─────────────────────────────────────────────
def build_color_maps(df_main, df_comm):
    palette = (
        px.colors.qualitative.Pastel +
        px.colors.qualitative.Set3 +
        px.colors.qualitative.Set2 +
        px.colors.qualitative.Safe
    ) * 10

    all_nations = sorted(
        pd.concat([
            df_main["국적"] if not df_main.empty else pd.Series(),
            df_comm["국적"] if not df_comm.empty else pd.Series(),
        ]).dropna().unique()
    )
    nation_map = {n: palette[i] for i, n in enumerate(all_nations)}
    nation_map["중국"] = "#81C784"
    nation_map["일본"] = "#64B5F6"

    all_regions = sorted(df_main["권역"].dropna().unique()) if not df_main.empty else []
    region_map = {r: palette[i] for i, r in enumerate(all_regions)}

    all_agents = sorted(df_comm["에이전트"].dropna().unique()) if not df_comm.empty else []
    agent_map = {a: palette[i] for i, a in enumerate(all_agents)}

    return nation_map, region_map, agent_map


# ─────────────────────────────────────────────
# 7. 공통 UI 컴포넌트
# ─────────────────────────────────────────────
def render_metric_row(metrics: list):
    """
    metrics: [(label, value_str, delta_str or None), ...]
    """
    cols = st.columns(len(metrics))
    for col, (label, value, delta) in zip(cols, metrics):
        with col:
            if delta is not None:
                st.metric(label, value, delta)
            else:
                st.metric(label, value)


def render_diff_table(table_df, group_col, sel_month, prev_month, prev_exists):
    """
    증감 테이블을 렌더링하는 공통 함수
    table_df: ['그룹컬럼', '당월매출', '전월매출', '증감액'] 포함
    """
    table_df = table_df.copy()

    total_row = pd.DataFrame([{
        group_col:  "[ 총 합계 ]",
        "당월매출": table_df["당월매출"].sum(),
        "전월매출": table_df["전월매출"].sum(),
        "증감액":   table_df["증감액"].sum(),
    }])
    table_df = pd.concat([table_df, total_row], ignore_index=True)
    table_df[f"{sel_month}"] = table_df["당월매출"].apply(lambda x: f"{int(x):,}")

    if prev_exists:
        table_df[f"{prev_month}(전월)"] = table_df["전월매출"].apply(lambda x: f"{int(x):,}")
        table_df["전월대비"] = table_df.apply(
            lambda r: format_diff(r["당월매출"], r["전월매출"]), axis=1
        )
        display_cols = [group_col, f"{prev_month}(전월)", f"{sel_month}", "전월대비"]
        col_config = {
            f"{prev_month}(전월)": st.column_config.TextColumn(alignment="right"),
            f"{sel_month}":       st.column_config.TextColumn(alignment="right"),
            "전월대비":            st.column_config.TextColumn(alignment="right"),
        }
    else:
        display_cols = [group_col, f"{sel_month}"]
        col_config = {f"{sel_month}": st.column_config.TextColumn(alignment="right")}

    st.markdown(
        "<p style='text-align:right;color:#94a3b8;font-size:0.78rem;'>(단위: 원)</p>",
        unsafe_allow_html=True,
    )
    st.dataframe(
        table_df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
    )


def render_ai_report(curr_total, prev_total, curr_groups, prev_groups, label_name="국가"):
    """AI 실적 분석 리포트 공통 렌더링"""
    st.markdown("### 💡 AI 자동 분석 리포트")
    if prev_total <= 0:
        st.info("비교 데이터가 부족하여 분석을 생략합니다.")
        return

    diff_amt = curr_total - prev_total
    growth = (diff_amt / prev_total) * 100

    if growth > 0:
        st.success(f"📈 **전월 대비 총매출 성장!** (+{diff_amt:,.0f}원 / +{growth:.1f}%)")
    elif growth < 0:
        st.warning(f"📉 **전월 대비 총매출 감소.** ({diff_amt:,.0f}원 / {growth:.1f}%)")
    else:
        st.info("전월 대비 변동 없음.")

    group_diff = curr_groups.subtract(prev_groups, fill_value=0)
    if not group_diff.empty:
        top_g = group_diff.idxmax()
        top_amt = group_diff.max()
        if top_amt > 0:
            p_amt = prev_groups.get(top_g, 0)
            rate_str = f" / +{(top_amt / p_amt * 100):.1f}%" if p_amt > 0 else " / 순증가(신규)"
            st.info(f"🔥 **최대 성장 {label_name}:** **{top_g}** (+{top_amt:,.0f}원{rate_str})")

        bot_g = group_diff.idxmin()
        bot_amt = group_diff.min()
        if bot_amt < 0:
            p_amt_b = prev_groups.get(bot_g, 0)
            rate_str_b = f" / {(bot_amt / p_amt_b * 100):.1f}%" if p_amt_b > 0 else ""
            st.error(f"🔻 **최대 감소 {label_name}:** **{bot_g}** ({bot_amt:,.0f}원{rate_str_b})")


def render_trend_chart(trend_df, group_col, color_map, chronological_months, title="월별 성장 추이", value_col="매출액_숫자"):
    """스택 바 + 라인 추이 차트 공통 렌더링"""
    st.subheader(f"📈 {title}")
    fig = go.Figure()

    for item in trend_df[group_col].unique():
        d = trend_df[trend_df[group_col] == item]
        fig.add_trace(go.Bar(
            x=d["매출월"], y=d[value_col],
            name=item, text=item,
            textposition="auto",
            marker_color=color_map.get(item, "#cccccc"),
        ))

    tot_series = (
        trend_df.groupby("매출월")[value_col]
        .sum()
        .reindex(chronological_months)
        .fillna(0)
    )
    fig.add_trace(go.Scatter(
        x=tot_series.index,
        y=tot_series.values,
        name="총합",
        line=dict(color="#1e293b", width=3),
        mode="lines+markers+text",
        text=[format_amount(v) for v in tot_series.values],
        textposition="top center",
    ))

    t_vals, t_txts = get_dynamic_ticks(tot_series.max())
    fig.update_layout(
        barmode="stack",
        hovermode="x unified",
        height=480,
        xaxis={"categoryorder": "array", "categoryarray": chronological_months},
        yaxis=dict(tickmode="array", tickvals=t_vals, ticktext=t_txts),
        bargap=0.4,
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# 8. 데이터 로딩 실행
# ─────────────────────────────────────────────
with st.spinner("📡 데이터 불러오는 중..."):
    df_main_raw, df_comm_raw, load_errors = load_all_data()

# 에러 표시
if load_errors:
    with st.sidebar.expander("⚠️ 데이터 로딩 오류", expanded=False):
        for err in load_errors:
            st.sidebar.warning(err)

df_main = add_date_columns(df_main_raw.copy(), "수납일") if not df_main_raw.empty else pd.DataFrame()
df_comm = add_date_columns(df_comm_raw.copy(), "날짜")   if not df_comm_raw.empty else pd.DataFrame()

# 날짜 목록
all_dates = pd.concat([
    df_main[["월순서", "매출월"]] if not df_main.empty and "월순서" in df_main.columns else pd.DataFrame(),
    df_comm[["월순서", "매출월"]] if not df_comm.empty and "월순서" in df_comm.columns else pd.DataFrame(),
]).drop_duplicates().sort_values("월순서")
CHRONOLOGICAL_MONTHS = all_dates["매출월"].dropna().tolist()

# 색상 맵
NATION_MAP, REGION_MAP, AGENT_MAP = build_color_maps(df_main, df_comm)


# ─────────────────────────────────────────────
# 9. 사이드바 네비게이션
# ─────────────────────────────────────────────
st.sidebar.title("🏨 온리프 해외 매출")
menu = st.sidebar.radio("메뉴 이동", ["🌐 온리프 해외매출 전체", "💸 수수료 매출(에이전트별)"])
month_list = sorted(CHRONOLOGICAL_MONTHS, reverse=True)

if not month_list:
    st.error("❌ 데이터에서 날짜 정보를 찾을 수 없습니다. Google Sheets 연결을 확인해주세요.")
    st.stop()

sel_month = st.sidebar.selectbox("📅 조회 월 선택", month_list)
idx = month_list.index(sel_month)
prev_month = month_list[idx + 1] if idx < len(month_list) - 1 else None


# ─────────────────────────────────────────────
# 10. 메뉴 1: 온리프 해외매출 전체
# ─────────────────────────────────────────────
if menu == "🌐 온리프 해외매출 전체":
    view_mode = st.sidebar.radio("🔎 분석 기준", ["국가별", "권역별"])
    group_col = "국적" if view_mode == "국가별" else "권역"
    color_map = NATION_MAP if view_mode == "국가별" else REGION_MAP

    st.title(f"🌐 {sel_month} 온리프 해외매출 전체")

    if "매출월" not in df_main.columns:
        st.error("날짜 데이터를 불러올 수 없습니다.")
        st.stop()

    m_df      = df_main[df_main["매출월"] == sel_month]
    total_rev = m_df["매출액_숫자"].sum()

    curr_comm_df = df_comm[df_comm["매출월"] == sel_month] if not df_comm.empty else pd.DataFrame()
    comm_rev     = curr_comm_df["매출액"].sum() if not curr_comm_df.empty else 0
    non_comm_rev = total_rev - comm_rev
    anpa_fee     = total_rev * ANPA_FEE_RATE

    # 전월 데이터
    prev_total = prev_comm_rev = prev_non_comm_rev = prev_anpa_fee = 0
    prev_m_df = pd.DataFrame()
    if prev_month:
        prev_m_df        = df_main[df_main["매출월"] == prev_month]
        prev_total       = prev_m_df["매출액_숫자"].sum()
        prev_comm_df     = df_comm[df_comm["매출월"] == prev_month] if not df_comm.empty else pd.DataFrame()
        prev_comm_rev    = prev_comm_df["매출액"].sum() if not prev_comm_df.empty else 0
        prev_non_comm_rev = prev_total - prev_comm_rev
        prev_anpa_fee    = prev_total * ANPA_FEE_RATE

    def _delta(curr, prev):
        if prev <= 0: return None
        rate = (curr - prev) / prev * 100
        sign = "+" if rate >= 0 else ""
        return f"{sign}{rate:.1f}%"

    # ── KPI 카드 ──
    m1, m2, m3, _, m4 = st.columns([1, 1, 1, 0.08, 1.2])
    with m1:
        st.metric("총 매출액 (VAT 제외)", f"{total_rev:,.0f}원", _delta(total_rev, prev_total))
    with m2:
        st.metric("수수료 미지급 매출", f"{non_comm_rev:,.0f}원", _delta(non_comm_rev, prev_non_comm_rev))
    with m3:
        st.metric("수수료 지급 매출", f"{comm_rev:,.0f}원", _delta(comm_rev, prev_comm_rev))
    with _:
        st.markdown("<div style='border-left:2px solid #e2e8f0;height:80px;margin:auto;width:2px;'></div>", unsafe_allow_html=True)
    with m4:
        st.metric("💡 앤파 컨설팅수수료(20%)", f"{anpa_fee:,.0f}원", _delta(anpa_fee, prev_anpa_fee))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI 리포트 ──
    with st.container():
        curr_groups = m_df.groupby("국적")["매출액_숫자"].sum()
        prev_groups = prev_m_df.groupby("국적")["매출액_숫자"].sum() if not prev_m_df.empty else pd.Series(dtype=float)
        render_ai_report(total_rev, prev_total, curr_groups, prev_groups, label_name="국가")

        # 역대 최고 체크
        if total_rev > 0 and total_rev == df_main.groupby("매출월")["매출액_숫자"].sum().max():
            st.info("🏆 **역대 최고 월 매출 기록!**")

    st.divider()

    # ── 파이차트 + 테이블 ──
    c1, c2 = st.columns([1, 1.2])
    with c1:
        n_df = m_df.groupby(group_col)["매출액_숫자"].sum().reset_index()
        n_df = n_df[n_df["매출액_숫자"] > 0]
        pie_total = n_df["매출액_숫자"].sum()

        fig_pie = px.pie(
            n_df, values="매출액_숫자", names=group_col,
            hole=0.4, color=group_col, color_discrete_map=color_map,
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(
            annotations=[dict(
                text=f"총 매출액<br><b>{pie_total:,.0f}원</b>",
                x=0.5, y=0.5, font_size=13, showarrow=False,
            )],
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader(f"📑 {view_mode} 상세 실적")
        curr_grp = m_df.groupby(group_col)["매출액_숫자"].sum().reset_index().rename(columns={"매출액_숫자": "당월매출"})
        if prev_month and not prev_m_df.empty:
            prev_grp = prev_m_df.groupby(group_col)["매출액_숫자"].sum().reset_index().rename(columns={"매출액_숫자": "전월매출"})
            tbl = pd.merge(curr_grp, prev_grp, on=group_col, how="outer").fillna(0)
        else:
            tbl = curr_grp.copy()
            tbl["전월매출"] = 0
        tbl["증감액"] = tbl["당월매출"] - tbl["전월매출"]
        tbl = tbl.sort_values("당월매출", ascending=False)
        render_diff_table(tbl, group_col, sel_month, prev_month or "", bool(prev_month))

    # ── 권역별 드릴다운 (국가별 선택 시) ──
    if view_mode == "국가별":
        st.divider()
        st.subheader("🗺️ 권역별 국가 구성 드릴다운")
        regions = m_df["권역"].dropna().unique()
        if len(regions) > 0:
            tabs = st.tabs(list(regions))
            for tab, region in zip(tabs, regions):
                with tab:
                    reg_df = m_df[m_df["권역"] == region]
                    reg_curr = reg_df.groupby("국적")["매출액_숫자"].sum().reset_index().rename(columns={"매출액_숫자": "당월매출"})
                    if prev_month and not prev_m_df.empty:
                        reg_prev_df = prev_m_df[prev_m_df["권역"] == region]
                        reg_prev = reg_prev_df.groupby("국적")["매출액_숫자"].sum().reset_index().rename(columns={"매출액_숫자": "전월매출"})
                        reg_tbl = pd.merge(reg_curr, reg_prev, on="국적", how="outer").fillna(0)
                    else:
                        reg_tbl = reg_curr.copy()
                        reg_tbl["전월매출"] = 0
                    reg_tbl["증감액"] = reg_tbl["당월매출"] - reg_tbl["전월매출"]
                    reg_tbl = reg_tbl.sort_values("당월매출", ascending=False)
                    render_diff_table(reg_tbl, "국적", sel_month, prev_month or "", bool(prev_month))

    st.divider()

    # ── 월별 추이 차트 ──
    trend_df = df_main.groupby(["월순서", "매출월", group_col])["매출액_숫자"].sum().reset_index().sort_values("월순서")
    render_trend_chart(trend_df, group_col, color_map, CHRONOLOGICAL_MONTHS,
                       title=f"전체 월별 성장 추이 ({view_mode} 기준)", value_col="매출액_숫자")


# ─────────────────────────────────────────────
# 11. 메뉴 2: 수수료 매출 (에이전트별)
# ─────────────────────────────────────────────
else:
    agent_options = ["전체"] + sorted(df_comm["에이전트"].dropna().unique().tolist())
    sel_agent = st.sidebar.selectbox("🧑‍💼 에이전트 상세 필터", agent_options)

    if sel_agent == "전체":
        page_df    = df_comm.copy()
        g_col      = "에이전트"
        page_title = "수수료 매출 전체 분석"
    else:
        page_df    = df_comm[df_comm["에이전트"] == sel_agent].copy()
        g_col      = "국적"
        page_title = f"[{sel_agent}] 에이전트 상세 분석"

    st.title(f"💸 {sel_month} {page_title}")

    if page_df.empty:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
        st.stop()

    curr_comm = page_df[page_df["매출월"] == sel_month]
    total_comm_rev = curr_comm["매출액"].sum()
    c_paid_comm    = curr_comm["지급수수료"].sum()
    c_net_rev      = curr_comm["실매출액"].sum()

    # 전월
    p_comm_total = p_paid_comm = p_net_rev = 0
    p_comm_df = pd.DataFrame()
    if prev_month:
        p_comm_df    = page_df[page_df["매출월"] == prev_month]
        p_comm_total = p_comm_df["매출액"].sum()
        p_paid_comm  = p_comm_df["지급수수료"].sum()
        p_net_rev    = p_comm_df["실매출액"].sum()

    def _d(curr, prev):
        if prev <= 0: return None
        r = (curr - prev) / prev * 100
        return f"{'+'if r>=0 else ''}{r:.1f}%"

    # ── KPI 카드 ──
    m1, m2, m3 = st.columns(3)
    label = "총 수납액 합계" if sel_agent == "전체" else f"[{sel_agent}] 총 수납액"
    with m1:
        st.metric(label, f"{total_comm_rev:,.0f}원", _d(total_comm_rev, p_comm_total))
    with m2:
        st.metric("지급수수료", f"{c_paid_comm:,.0f}원", _d(c_paid_comm, p_paid_comm))
    with m3:
        st.metric("실매출액(총수납액-지급수수료)", f"{c_net_rev:,.0f}원", _d(c_net_rev, p_net_rev))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI 리포트 ──
    with st.container():
        curr_g = curr_comm.groupby(g_col)["매출액"].sum()
        prev_g = p_comm_df.groupby(g_col)["매출액"].sum() if not p_comm_df.empty else pd.Series(dtype=float)
        label_name = "에이전트" if sel_agent == "전체" else "국가"
        render_ai_report(total_comm_rev, p_comm_total, curr_g, prev_g, label_name=label_name)

        if total_comm_rev > 0 and total_comm_rev == page_df.groupby("매출월")["매출액"].sum().max():
            st.info("🏆 **역대 최고치 경신!**")

    st.divider()

    # ── 에이전트 전체: 국가 구성비 가로 바 차트 + 정산 테이블 ──
    if sel_agent == "전체":
        st.subheader(f"🗺️ {sel_month} 에이전트별 국가 구성비")
        if not curr_comm.empty:
            comp = curr_comm.groupby(["에이전트", "국적"])["매출액"].sum().reset_index()
            comp = comp[comp["매출액"] > 0]

            bar_max  = comp.groupby("에이전트")["매출액"].sum().max() if not comp.empty else 0
            b_vals, b_txts = get_dynamic_ticks(bar_max)

            fig_bar = px.bar(
                comp, x="매출액", y="에이전트", color="국적",
                orientation="h", text="국적",
                color_discrete_map=NATION_MAP,
            )
            fig_bar.update_traces(textposition="inside")
            fig_bar.update_layout(
                barmode="stack", height=400,
                xaxis=dict(tickmode="array", tickvals=b_vals, ticktext=b_txts),
                plot_bgcolor="#fafafa", paper_bgcolor="#ffffff",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("📑 상세 정산 내역")
        curr_grp = curr_comm.groupby("에이전트")["매출액"].sum().reset_index().rename(columns={"매출액": "당월매출"})
        if p_comm_total > 0:
            prev_grp = p_comm_df.groupby("에이전트")["매출액"].sum().reset_index().rename(columns={"매출액": "전월매출"})
            tbl = pd.merge(curr_grp, prev_grp, on="에이전트", how="outer").fillna(0)
        else:
            tbl = curr_grp.copy()
            tbl["전월매출"] = 0
        tbl["증감액"] = tbl["당월매출"] - tbl["전월매출"]
        tbl = tbl.sort_values("당월매출", ascending=False)
        tbl["에이전트(수수료율)"] = tbl["에이전트"].apply(
            lambda x: f"{x}({int(COMMISSION_RATES.get(x, 0.15)*100)}%)"
        )
        tbl2 = tbl.rename(columns={"에이전트(수수료율)": "에이전트"})
        tbl2["에이전트"] = tbl["에이전트(수수료율)"]
        render_diff_table(tbl2.rename(columns={"에이전트": "에이전트(수수료율)"}),
                          "에이전트(수수료율)", sel_month, prev_month or "", bool(prev_month))

    # ── 개별 에이전트: 국가 파이 + 테이블 ──
    else:
        st.subheader(f"🗺️ {sel_month} [{sel_agent}] 소속 국가 구성비")
        if not curr_comm.empty:
            col1, col2 = st.columns([1, 1.2])
            with col1:
                comp = curr_comm.groupby("국적")["매출액"].sum().reset_index()
                comp = comp[comp["매출액"] > 0]
                comp_total = comp["매출액"].sum()
                fig_pie2 = px.pie(
                    comp, values="매출액", names="국적",
                    hole=0.4, color="국적", color_discrete_map=NATION_MAP,
                )
                fig_pie2.update_traces(textinfo="percent+label")
                fig_pie2.update_layout(
                    annotations=[dict(
                        text=f"총 수납액<br><b>{comp_total:,.0f}원</b>",
                        x=0.5, y=0.5, font_size=13, showarrow=False,
                    )],
                    showlegend=False,
                )
                st.plotly_chart(fig_pie2, use_container_width=True)

            with col2:
                st.subheader("📑 상세 정산 내역")
                curr_grp = curr_comm.groupby("국적")["매출액"].sum().reset_index().rename(columns={"매출액": "당월매출"})
                if p_comm_total > 0:
                    prev_grp = p_comm_df.groupby("국적")["매출액"].sum().reset_index().rename(columns={"매출액": "전월매출"})
                    tbl = pd.merge(curr_grp, prev_grp, on="국적", how="outer").fillna(0)
                else:
                    tbl = curr_grp.copy()
                    tbl["전월매출"] = 0
                tbl["증감액"] = tbl["당월매출"] - tbl["전월매출"]
                tbl = tbl.sort_values("당월매출", ascending=False)
                render_diff_table(tbl, "국적", sel_month, prev_month or "", bool(prev_month))

    st.divider()

    # ── 월별 수수료 추이 ──
    chart_sub = "에이전트별 누적" if sel_agent == "전체" else "국가(국적)별 누적"
    ctrend_df = page_df.groupby(["월순서", "매출월", g_col])["매출액"].sum().reset_index().sort_values("월순서")
    c_map = AGENT_MAP if sel_agent == "전체" else NATION_MAP
    render_trend_chart(ctrend_df, g_col, c_map, CHRONOLOGICAL_MONTHS,
                       title=f"월별 수수료 매출 추이 ({chart_sub})", value_col="매출액")
