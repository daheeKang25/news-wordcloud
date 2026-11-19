from ch8_1 import naver_new_search
from kiwipiepy import Kiwi
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from  openai import OpenAI
from dotenv import load_dotenv
# from os import getenv
import json
from pathlib import Path

# 로컬 환경변수 불러오기
load_dotenv()

# 로컬 환경에서는 .env 사용
# key = os.getenv("OPENAI_API_KEY")

# Streamlit Cloud에서는 Secrets 우선 사용
try:
    key = st.secrets.get("OPENAI_API_KEY", key)
except FileNotFoundError:
    pass
client = OpenAI(api_key=key)

def get_stop_words(keyword, word_count):
    prompt = f'''
        검색어: {keyword}
        단어별 등장 빈도:
        {word_count}
        위 데이터는 뉴스에서 추출한 명사와 등장 빈도입니다.
        뉴스의 주요 이슈를 파악하기 위한 워드클라우드를 생성하려고 합니다.
        다음 기준에 따라 불용어를 선정하세요.
    
        불용어 선정 기준:
        1. 검색어 자체는 반드시 유지하세요.
        2. 검색어를 구성하는 개별 단어나 약칭이 중복되면 제거하세요.
        3. 동일한 대상을 의미하는 여러 표현은 검색어를 제외하고 제거하세요.
        4. 기자, 이번, 관련 등 뉴스에서 관용적으로 사용되는 단어는 제거하세요.
        5. 대상, 진행, 개최, 전문 등 주요 이슈를 구분하기 어려운 일반적인 단어도 검토하세요.
        6. 취업, 교육, 기업, 정책 등 뉴스의 주요 주제를 나타내는 단어는 유지하세요.
        7. 검색어와 관련성이 낮다는 이유만으로 단어를 제거하지 마세요.
        8. 반드시 제공된 단어 중에서만 선정하세요.
        9. 단어의 등장 빈도가 높다는 이유만으로 제거하지 마세요.
    
        예시:
        검색어가 '한양여자대학교'라면
        - 반드시 유지: 한양여자대학교
        - 반드시 제거 후보: 한양, 여자, 여대, 대학교, 대학, 한양여대
    
        검색어가 '삼성전자'라면
        - 반드시 유지: 삼성전자
        - 반드시 제거 후보: 삼성, 전자 (동일 기업을 중복 지칭하는 경우)
    
        출력 형식(Json):
        {{"불용어": ["단어1", "단어2", "단어3"]}}
        다른 설명이나 번호는 출력하지 마세요.
        '''
    response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role':'user','content':prompt}],
    response_format={'type':'json_object'}
)
    stop_words = json.loads(response.choices[0].message.content).get('불용어')
    return stop_words

def generate_wordcloud(keyword, text):
    BASE_DIR = Path(__file__).resolve().parent
    font_path = BASE_DIR / "font" / "Moneygraphy-Pixel.ttf"
    kiwi = Kiwi()
    tokens = kiwi.tokenize(text)
    nouns = [v.form for v in tokens if v.tag in ['NNG','NNP'] 
                 and len(v.form)>=2]
    stop_words = get_stop_words(keyword, nouns)
    nouns = [v for v in nouns if v not in stop_words]
    word_count = Counter(nouns)
    wc = WordCloud(font_path=str(font_path),
                   background_color='white', 
                   width=1200,
                   height=700)
    wc.generate_from_frequencies(word_count)
    fig = plt.figure()
    plt.imshow(wc)
    plt.axis('off')
    # plt.show()
    return fig

def make_new_text(results):
    news_text = ''
    for v in results:
        news_text+=v['title']+' '+v['description'] +'\n'
    return news_text

if __name__ =='__main__':
    keyword = '드림캐쳐 컴퍼니'
    results = naver_new_search(keyword)
    news_text = make_new_text(results)
    generate_wordcloud(keyword, news_text)
    
