from ch8_1 import naver_new_search
from kiwipiepy import Kiwi
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from pathlib import Path

def generate_wordcloud(keyword, text):
    BASE_DIR = Path(__file__).resolve().parent
    font_path = BASE_DIR / "font" / "Moneygraphy-Pixel.ttf"
    kiwi = Kiwi()
    tokens = kiwi.tokenize(text)
    nouns = [v.form for v in tokens if v.tag in ['NNG','NNP'] 
                 and len(v.form)>=2]
    stop_words = ['컴퍼니','드림캐쳐','드림캐쳐컴퍼니']
    nouns = [v for v in nouns if v not in stop_words]
    word_count = Counter(nouns)
    wc = WordCloud(font_path= str(font_path),
                   background_color='white', 
                   width=1200,
                   height=700)
    wc.generate_from_frequencies(word_count)
    fig = plt.figure()
    plt.imshow(wc)
    plt.axis('off')
    plt.show()

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
    