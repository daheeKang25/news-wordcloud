import streamlit as st
from ch8_3 import generate_wordcloud, make_new_text
from ch8_2 import naver_new_search
import pandas as pd

def main():
    st.set_page_config(layout='wide')
    st.title('AI 뉴스 워드클라우드')
    keyword = st.text_input('검색어를 입력하세요.')
    if 'results' not in st.session_state:
        st.session_state.results=None
    if 'fig' not in st.session_state:
        st.session_state.fig=None
    if st.button('검색 및 분석'):
        if not keyword.strip():
            st.warning('검색어를 입력하세요.')
        else:
            with st.spinner('뉴스 분석 중...'):
                try:
                    results = naver_new_search(keyword.strip())
                    if results:
                        news_text = make_new_text(results)
                        fig = generate_wordcloud(keyword.strip(), news_text)
                        st.session_state.results = results
                        st.session_state.fig = fig
                        
                    else:
                        st.warning('검색 결과가 없습니다.')
                except Exception as e:
                    st.error(f'오류 발생: {e}')
    if st.session_state.results is not None:
        st.subheader('뉴스 검색 결과')
        df = pd.DataFrame(st.session_state.results)
        df.columns=['날짜','제목','요약문','링크']
        st.dataframe(
            df,
            hide_index=True,
            width='stretch',
            column_config={
                '링크':st.column_config.LinkColumn(
                    '기사 원문',
                    display_text='기사 열기'
                )
            }
        )
        st.subheader('뉴스 워드클라우드')
        st.pyplot(st.session_state.fig, width=1200)

if __name__ =='__main__':
    main()
