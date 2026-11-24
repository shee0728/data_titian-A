import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns

st.set_page_config(page_title="Titanic 대시보드", layout="wide")


@st.cache_data
def load_data():
    data = sns.load_dataset("titanic")
    for col in data.select_dtypes(include=["category"]).columns:
        data[col] = data[col].astype(str)
    return data


def filter_data(df, sexes, classes, age_range):
    min_age, max_age = age_range
    cond_sex = df["sex"].isin(sexes)
    cond_class = df["pclass"].isin(classes)
    if age_range == (0, 80):
        cond_age = ((df["age"] >= min_age) & (df["age"] <= max_age)) | df["age"].isna()
    else:
        cond_age = (df["age"] >= min_age) & (df["age"] <= max_age)
    return df[cond_sex & cond_class & cond_age]


def kpi(df):
    if df.empty:
        return (0, 0, 0)
    total_passengers = len(df)
    survival_rate = round(df["survived"].mean() * 100, 1)
    mean_age_raw = df["age"].mean()
    avg_age = 0 if pd.isna(mean_age_raw) else round(mean_age_raw, 1)
    return (total_passengers, survival_rate, avg_age)


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


st.title("타이타닉, 누가 살아남았나?")
df = load_data()

st.sidebar.header("검색 조건 필터")
sex_options = sorted(df["sex"].dropna().unique().tolist())
selected_sexes = st.sidebar.multiselect("성별 선택", options=sex_options, default=sex_options)

class_options = sorted(df["pclass"].dropna().unique().tolist())
selected_classes = st.sidebar.multiselect("객실 등급 선택", options=class_options, default=class_options)

selected_age_range = st.sidebar.slider("나이 범위 (세)", min_value=0, max_value=80, value=(0, 80))

if not selected_sexes or not selected_classes:
    st.warning("성별과 객실 등급을 각각 최소 1개 이상 선택해주세요.")
    st.stop()

filtered_df = filter_data(df, selected_sexes, selected_classes, selected_age_range)

if filtered_df.empty:
    st.warning("조건에 맞는 승객이 없습니다.")
    st.stop()

total_passengers, survival_rate, avg_age = kpi(filtered_df)

col1, col2, col3 = st.columns(3)
col1.metric("승객 수", f"{total_passengers}명")
col2.metric("생존율", f"{survival_rate}%")
col3.metric("평균 나이", f"{avg_age}세")

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(class_rate_bar(filtered_df), use_container_width=True)
with chart_col2:
    st.plotly_chart(age_hist(filtered_df), use_container_width=True)

with st.expander("데이터 보기"):
    st.dataframe(filtered_df, use_container_width=True)
