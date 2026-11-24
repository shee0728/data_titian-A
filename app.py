# ===== 1. 라이브러리 불러오기 =====
import streamlit as st
import pandas as pd
import plotly.express as px

# 가장 먼저 실행되는 Streamlit 설정 명령 배치
st.set_page_config(page_title="Titanic 대시보드", layout="wide")


# ===== 2. 데이터 로드 (캐싱 적용) =====
@st.cache_data
def load_data():
    # titanic.csv 파일을 한 번만 읽어와 메모리에 캐싱
    return pd.read_csv("titanic.csv")


# ===== 3. 데이터 필터링 및 KPI/차트 함수 정의 =====
# 조건(성별, 객실 등급, 나이 범위)에 맞는 승객 데이터만 필터링하는 함수
def filter_data(df, sexes, classes, age_range):
    min_age, max_age = age_range
    cond_sex = df["sex"].isin(sexes)
    cond_class = df["pclass"].isin(classes)
    if age_range == (0, 80):  # [수정]
        cond_age = ((df["age"] >= min_age) & (df["age"] <= max_age)) | df["age"].isna()  # [수정]
    else:  # [수정]
        cond_age = (df["age"] >= min_age) & (df["age"] <= max_age)  # [수정]
    filtered_df = df[cond_sex & cond_class & cond_age]
    return filtered_df


# 대시보드 상단 KPI 숫자 카드용 지표 3개를 계산하는 함수
def kpi(df):
    if df.empty:
        return (0, 0, 0)
    total_passengers = len(df)
    survival_rate = round(df["survived"].mean() * 100, 1)
    mean_age_raw = df["age"].mean()
    avg_age = 0 if pd.isna(mean_age_raw) else round(mean_age_raw, 1)
    return (total_passengers, survival_rate, avg_age)


# 객실 등급별 생존율(%) 막대그래프를 생성해 fig를 반환하는 함수
def class_rate_bar(df):
    rate_df = (
        df.groupby("pclass", as_index=False)["survived"]
        .mean()
        .assign(생존율=lambda x: (x["survived"] * 100).round(1))
    )
    rate_df["객실등급"] = rate_df["pclass"].astype(str) + "등급"
    fig = px.bar(
        rate_df,
        x="객실등급",
        y="생존율",
        text="생존율",
        title="객실 등급별 생존율 (%)",
        labels={"객실등급": "객실 등급", "생존율": "생존율 (%)"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_yaxes(range=[0, 110])
    return fig


# 생존 여부(survived)별 나이 히스토그램을 생성해 fig를 반환하는 함수
def age_hist(df):
    plot_df = df.copy()
    plot_df["생존여부"] = plot_df["survived"].map({0: "사망", 1: "생존"})
    fig = px.histogram(
        plot_df,
        x="age",
        color="생존여부",
        barmode="overlay",
        opacity=0.6,
        title="생존 여부별 승객 나이 분포",
        labels={"age": "나이 (세)", "생존여부": "생존 여부"},
        color_discrete_map={"생존": "#2E86AB", "사망": "#D9534F"},
    )
    fig.update_yaxes(title_text="승객 수 (명)")
    return fig


# ===== 4. 대시보드 제목 및 데이터 준비 =====
st.title("타이타닉, 누가 살아남았나?")

# 캐싱된 데이터 불러오기
df = load_data()


# ===== 5. 사이드바 필터 구성 =====
st.sidebar.header("검색 조건 필터")

# 성별 다중 선택 (기본값: 전체 선택)
sex_options = sorted(df["sex"].dropna().unique().tolist())
selected_sexes = st.sidebar.multiselect(
    "성별 선택",
    options=sex_options,
    default=sex_options
)

# 객실 등급 다중 선택 (기본값: 1, 2, 3등급 모두 선택)
class_options = sorted(df["pclass"].dropna().unique().tolist())
selected_classes = st.sidebar.multiselect(
    "객실 등급 선택",
    options=class_options,
    default=class_options
)

# 나이 범위 슬라이더 (0~80세, 기본값: 전체 범위)
selected_age_range = st.sidebar.slider(
    "나이 범위 (세)",
    min_value=0,
    max_value=80,
    value=(0, 80)
)


# ===== 6. 데이터 필터링 및 본문 출력 =====
if not selected_sexes or not selected_classes:  # [수정]
    st.warning("성별과 객실 등급을 각각 최소 1개 이상 선택해주세요.")  # [수정]
    st.stop()  # [수정]

# 사이드바 조건에 맞게 데이터 필터링 실행
