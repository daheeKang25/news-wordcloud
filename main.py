import altair as alt
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from news_analysis import (
    build_analysis, keyword_counts, make_network, make_wordcloud,
    rising_keywords, timeline_data, bucket_name,
)


st.set_page_config(
    page_title="News Insight | 뉴스 트렌드 대시보드",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container {max-width: 1480px; padding-top: 2.2rem;}
.hero {
    background: linear-gradient(115deg, #172957 0%, #245CE8 100%);
    border-radius: 22px; padding: 30px 38px; margin-bottom: 25px;
}
.hero h1 {color: white; margin: 0 0 10px 0; font-size: 2.2rem;}
.hero p {color: #D9E7FF; margin: 0; font-size: 1rem;}
.eyebrow {color: #9ABCFD; letter-spacing: .16em; font-size: .75rem; font-weight: 700;}
</style>
""", unsafe_allow_html=True)


def extract_choice(event, selection_name, field):
    try:
        selected = event.selection.get(selection_name, [])
        return selected[0].get(field) if selected else None
    except (AttributeError, IndexError, TypeError, KeyError):
        return None


def render_dashboard():
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">NEWS INSIGHT · AI ANALYTICS</div>
      <h1>뉴스 트렌드 대시보드</h1>
      <p>뉴스 검색 · AI 감성 및 요약 · 키워드 관계 · 언론사와 지역별 분석</p>
    </div>
    """, unsafe_allow_html=True)

    if "analysis" not in st.session_state:
        st.session_state.analysis = None
    if "chart_nonce" not in st.session_state:
        st.session_state.chart_nonce = 0

    # 새 검색을 시작할 때만 API/AI 호출; 아래 필터와 차트 클릭에는 API를 재호출하지 않음.
    with st.container(border=True):
        st.subheader("뉴스 검색 및 분석 설정")
        with st.form("search_form"):
            c1, c2, c3, c4 = st.columns([4, 1.5, 1.2, 1.6], vertical_alignment="bottom")
            with c1:
                keyword = st.text_input("검색 키워드", value="드림캐쳐 컴퍼니", placeholder="기업, 인물, 기술, 정책 등")
            with c2:
                period = st.selectbox("분석 기간", ["오늘", "최근 7일", "최근 30일"], index=1)
            with c3:
                limit = st.selectbox("최대 수집량", [100, 200, 300], index=0, format_func=lambda x: f"{x}건")
            with c4:
                use_ai = st.checkbox("AI 감성·요약", value=True, help="OpenAI API 비용이 발생함. 불용어 선정도 AI로 수행함.")
            submitted = st.form_submit_button("뉴스 검색 및 분석 시작", type="primary", width="stretch")

        if submitted:
            if not keyword.strip():
                st.warning("검색어를 입력해 주세요.")
            else:
                try:
                    with st.spinner("뉴스 수집, 형태소 처리 및 AI 분석을 진행합니다..."):
                        payload = build_analysis(keyword.strip(), period, limit, use_ai)
                    st.session_state.analysis = payload
                    st.session_state.chart_nonce += 1
                    if payload["articles"]:
                        st.success(f"'{keyword.strip()}' 뉴스 {len(payload['articles'])}건을 수집했습니다.")
                    else:
                        st.warning("선택한 기간의 검색 결과가 없습니다. 기간을 늘리거나 검색어를 바꿔 보세요.")
                except Exception as exc:
                    st.error(f"검색·분석 중 오류 발생: {exc}")

    payload = st.session_state.analysis
    if not payload or not payload["articles"]:
        st.info("검색어와 기간을 선택한 다음 분석을 시작하면 대시보드가 표시됩니다.")
        return

    articles = payload["articles"]
    stop_words = payload["stop_words"]
    active_period = payload["period"]
    st.caption(
        f"현재 분석: {payload['keyword']} · {active_period} · {len(articles)}건 수집 · "
        "네이버 뉴스 검색 결과 표본 (전체 기사 전수조사가 아님)"
    )
    for warning in payload["warnings"]:
        st.warning(warning)

    st.subheader("필터 및 지표")
    topics = sorted({a["topic"] for a in articles})
    publishers = sorted({a["publisher"] for a in articles})
    regions = sorted({a["region"] for a in articles})
    sentiments = sorted({a["sentiment"] for a in articles})

    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            topic_filter = st.selectbox("키워드·토픽", ["전체"] + topics)
        with f2:
            pub_filter = st.selectbox("언론사 / 출처 도메인", ["전체"] + publishers)
        with f3:
            region_filter = st.selectbox("기사 내 지역 언급", ["전체"] + regions)
        with f4:
            sentiment_filter = st.selectbox("AI 감성", ["전체"] + sentiments)

    filtered = [
        a for a in articles
        if (topic_filter == "전체" or a["topic"] == topic_filter)
        and (pub_filter == "전체" or a["publisher"] == pub_filter)
        and (region_filter == "전체" or a["region"] == region_filter)
        and (sentiment_filter == "전체" or a["sentiment"] == sentiment_filter)
    ]

    if not filtered:
        st.info("현재 필터에 해당하는 기사가 없습니다. 필터를 변경하세요.")
        return

    rising = rising_keywords(filtered, active_period, stop_words)
    analyzed = [a for a in filtered if a["sentiment"] in ("긍정", "부정", "중립")]
    pos_ratio = f"{sum(a['sentiment'] == '긍정' for a in analyzed) / len(analyzed):.0%}" if analyzed else "—"
    neg_ratio = f"{sum(a['sentiment'] == '부정' for a in analyzed) / len(analyzed):.0%}" if analyzed else "—"
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("수집 기사 수", f"{len(filtered):,}건", border=True)
    k2.metric("급증 키워드", f"{rising}개" if rising is not None else "—", border=True)
    k3.metric("긍정 기사 비율", pos_ratio, border=True)
    k4.metric("부정 기사 비율", neg_ratio, border=True)
    st.caption("급증 키워드: 마지막 활동 구간의 기사 언급 수가 직전 3개 활동 구간 평균의 2배 이상이며 최소 3건·평균 대비 2건 이상 증가한 단어. 선행 활동 구간이 부족하면 —로 표시함. 감성 비율은 분석된 기사만을 분모로 사용함.")

    st.divider()
    st.subheader("메인 트렌드 · 기사량 추이")
    timeline = timeline_data(filtered, active_period)
    spike_count = int(timeline["급증"].sum())
    st.caption(f"점 클릭: 해당 시간대/날짜 기사만 하단 피드에 표시 · 급증 시점 {spike_count}개 · 선택 해제는 차트에서 더블클릭")
    time_select = alt.selection_point(fields=["구간"], name="time_pick", on="click", clear="dblclick", toggle=False)
    line = alt.Chart(timeline).mark_line(color="#245CE8", strokeWidth=3).encode(
        x=alt.X("구간:N", sort=timeline["구간"].tolist(), title="시간 구간"),
        y=alt.Y("기사 수:Q", title="기사 수"),
        tooltip=["구간:N", "기사 수:Q", "급증:N"],
    )
    dots = alt.Chart(timeline).mark_circle(size=110).encode(
        x=alt.X("구간:N", sort=timeline["구간"].tolist()),
        y="기사 수:Q",
        color=alt.condition("datum['급증']", alt.value("#EC5B56"), alt.value("#245CE8")),
        tooltip=["구간:N", "기사 수:Q", "급증:N"],
    )
    trend_event = st.altair_chart(
        (line + dots).add_params(time_select).properties(height=290),
        width="stretch", key=f"trend_{st.session_state.chart_nonce}", on_select="rerun",
    )
    picked_time = extract_choice(trend_event, "time_pick", "구간")
    if picked_time not in timeline["구간"].tolist():
        picked_time = None

    st.divider()
    st.subheader("키워드 분포 및 연관 관계")
    counts = keyword_counts(filtered, stop_words)
    wc_col, bars_col = st.columns([1.2, 1])
    with wc_col:
        with st.container(border=True):
            st.markdown("**워드클라우드**")
            try:
                fig = make_wordcloud(filtered, stop_words)
                if fig is None:
                    st.info("표시할 키워드가 없습니다.")
                else:
                    st.pyplot(fig, width="stretch")
                    plt.close(fig)
            except (OSError, ValueError) as exc:
                st.warning(f"워드클라우드 생성 실패: {exc}")
    with bars_col:
        with st.container(border=True):
            st.markdown("**상위 키워드 TOP 15**")
            if counts:
                top_df = pd.DataFrame(counts.most_common(15), columns=["키워드", "빈도"])
                keyword_select = alt.selection_point(fields=["키워드"], name="keyword_pick", on="click", clear="dblclick", toggle=False)
                top_chart = alt.Chart(top_df).mark_bar(cornerRadiusEnd=5).encode(
                    x=alt.X("빈도:Q", title="등장 횟수"),
                    y=alt.Y("키워드:N", sort="-x", title=None),
                    color=alt.value("#527FEA"),
                    tooltip=["키워드:N", "빈도:Q"],
                ).add_params(keyword_select).properties(height=360)
                keyword_event = st.altair_chart(
                    top_chart, width="stretch", key=f"keywords_{st.session_state.chart_nonce}", on_select="rerun"
                )
                picked_keyword = extract_choice(keyword_event, "keyword_pick", "키워드")
                if picked_keyword not in set(top_df["키워드"]):
                    picked_keyword = None
            else:
                st.info("표시할 키워드가 없습니다.")
                picked_keyword = None

    net_col, pub_col = st.columns([1, 1])
    with net_col:
        with st.container(border=True):
            st.markdown("**키워드 공동 등장 네트워크**")
            st.caption("같은 기사 제목·요약문에서 함께 등장한 키워드 사이의 관계임. 인과관계가 아님.")
            try:
                fig = make_network(filtered, stop_words)
                if fig is None:
                    st.info("네트워크 연결을 계산할 만큼 함께 등장한 키워드가 없습니다.")
                else:
                    st.pyplot(fig, width="stretch")
                    plt.close(fig)
            except (OSError, ValueError) as exc:
                st.warning(f"관계망 시각화 실패: {exc}")
    with pub_col:
        with st.container(border=True):
            st.markdown("**언론사/출처 도메인별 보도량·논조**")
            st.caption("막대 클릭: 해당 출처로 기사 피드 필터링. 출처명은 원문 도메인 기준임.")
            source_df = pd.DataFrame([
                {"출처": a["publisher"], "감성": a["sentiment"]}
                for a in filtered
            ])
            top_publishers = source_df["출처"].value_counts().head(12).index.tolist()
            pub_counts = (
                source_df[source_df["출처"].isin(top_publishers)]
                .groupby(["출처", "감성"]).size().reset_index(name="기사 수")
            )
            publisher_select = alt.selection_point(fields=["출처"], name="publisher_pick", on="click", clear="dblclick", toggle=False)
            pub_chart = alt.Chart(pub_counts).mark_bar().encode(
                x=alt.X("기사 수:Q", title="기사 수"),
                y=alt.Y("출처:N", sort="-x", title=None),
                color=alt.Color("감성:N", scale=alt.Scale(
                    domain=["긍정", "중립", "부정", "미분석"],
                    range=["#39A97C", "#95A3B9", "#E57373", "#D4D9E3"],
                )),
                tooltip=["출처:N", "감성:N", "기사 수:Q"],
            ).add_params(publisher_select).properties(height=310)
            pub_event = st.altair_chart(
                pub_chart, width="stretch", key=f"publisher_{st.session_state.chart_nonce}", on_select="rerun"
            )
            picked_publisher = extract_choice(pub_event, "publisher_pick", "출처")
            if picked_publisher not in set(top_publishers):
                picked_publisher = None

    st.divider()
    st.subheader("주제·지역별 기사 분포")
    dist_cols = st.columns(2)
    for col, field, title in [
        (dist_cols[0], "topic", "주제 카테고리 분포"),
        (dist_cols[1], "region", "기사 내 지역 언급 분포"),
    ]:
        with col:
            with st.container(border=True):
                st.markdown("**" + title + "**")
                dist = pd.Series([a[field] for a in filtered]).value_counts().reset_index()
                dist.columns = ["항목", "기사 수"]
                chart = alt.Chart(dist.head(14)).mark_bar(cornerRadiusEnd=5, color="#6392EC").encode(
                    x=alt.X("기사 수:Q"), y=alt.Y("항목:N", sort="-x", title=None),
                    tooltip=["항목:N", "기사 수:Q"],
                ).properties(height=270)
                st.altair_chart(chart, width="stretch")

    st.divider()
    st.subheader("기사 피드 · 상세 분석")
    if any([picked_time, picked_keyword, picked_publisher]):
        st.info("차트 선택 적용: " + " · ".join(
            label for label in [
                f"시간 {picked_time}" if picked_time else "",
                f"키워드 {picked_keyword}" if picked_keyword else "",
                f"출처 {picked_publisher}" if picked_publisher else "",
            ] if label
        ))
        if st.button("차트 선택 초기화"):
            st.session_state.chart_nonce += 1
            st.rerun()

    feed = [
        a for a in filtered
        if (not picked_time or bucket_name(a["published_at"], active_period) == picked_time)
        and (not picked_keyword or picked_keyword in a["terms"])
        and (not picked_publisher or a["publisher"] == picked_publisher)
    ]
    feed.sort(key=lambda a: a["published_at"], reverse=True)
    st.caption(f"현재 필터·선택에 해당하는 기사 {len(feed)}건 · AI 요약은 기사 본문이 아닌 제목·검색요약 기반임")
    if not feed:
        st.info("선택한 차트 포인트에 해당하는 기사가 없습니다. 차트 선택을 해제하세요.")
        return

    feed_df = pd.DataFrame([{
        "날짜": a["date"], "제목": a["title"], "언론사/출처": a["publisher"],
        "주제": a["topic"], "지역(언급)": a["region"], "감성": a["sentiment"],
        "AI 요약": a["ai_summary"] or "미생성", "원문": a["link"],
    } for a in feed])

    table_event = st.dataframe(
        feed_df, hide_index=True, width="stretch", height=390,
        on_select="rerun", selection_mode="single-row", key=f"feed_{st.session_state.chart_nonce}",
        column_config={
            "원문": st.column_config.LinkColumn("기사 원문", display_text="원문 열기"),
            "AI 요약": st.column_config.TextColumn("AI 요약", width="large"),
            "제목": st.column_config.TextColumn("기사 제목", width="large"),
        },
    )
    selected_rows = table_event.selection.rows
    if selected_rows and 0 <= selected_rows[0] < len(feed):
        a = feed[selected_rows[0]]
        with st.container(border=True):
            st.markdown("**선택한 기사 상세 보기**")
            st.write(a["title"])
            st.caption(f"{a['date']} · {a['publisher']} · {a['topic']} · {a['sentiment']}")
            st.write("AI 요약: " + (a["ai_summary"] or "생성되지 않음"))
            st.write("검색 결과 요약문: " + a["description"])
            if a["link"].startswith(("https://", "http://")):
                st.link_button("원문 열기", a["link"])

    st.download_button(
        "CSV 다운로드", data=feed_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="news_insight_articles.csv", mime="text/csv", type="secondary",
    )
    st.caption("데이터 해석 유의사항: 검색 API가 반환한 기사 표본만 분석함. 원문 도메인으로 언론사 추정, 지역명 단순 언급 매칭, AI 논조/요약은 제목·요약문 기반 추정임. 급증 지표는 표본 내 변화이며 실시간 전체 여론을 의미하지 않음.")


if __name__ == "__main__":
    render_dashboard()
