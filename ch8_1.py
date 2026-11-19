import requests, json
from os import getenv
from dotenv import load_dotenv
from datetime import datetime as dd

load_dotenv()
n_id = getenv('X-NCP-APIGW-API-KEY-ID')
n_pw = getenv('X-NCP-APIGW-API-KEY')

def naver_new_search(keyword):
    
    query = {'query':keyword,'display':100}
    key = {'X-NCP-APIGW-API-KEY-ID':n_id, 'X-NCP-APIGW-API-KEY':n_pw}
    url = 'https://naverapihub.apigw.ntruss.com/search/v1/news'
    res = requests.get(url, params=query, headers=key).text
    data = json.loads(res)
    result = []
    for i, v in enumerate(data['items']):
        title=v['title'].replace('<b>','').replace('</b>','').replace('&quot;','"').replace('&lt;','<').replace('&gt;','>')
        link = v['link']
        date = v['pubDate']
        date = dd.strptime(date,'%a, %d %b %Y %H:%M:%S %z')
        date = date.strftime('%Y%m%d')
        description = v['description'].replace('<b>','').replace('</b>','').replace('&quot;','"').replace('amp;','').replace('&lt;','<').replace('&gt;','>')
        news = {'date':date,'title':title,'description':description,'link':link}
        result.append(news)
    return result

if __name__ =='__main__':
    results = naver_new_search('드림캐쳐컴퍼니')
    for i, v in enumerate(results):
        print(i+1, v)

