import requests

class youtube_request():
    basic_payload = {'safeSearch': 'none', 'orderby': 'relevance',
            'max-results': 19, 'paid-content': 'false',
            'v': 2, 'start-index': 1, 'alt': 'jsonc',
            'category': 'Music'}
    headers =  {'User-Agent': "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"}
    url = "https://gdata.youtube.com/feeds/api/videos"

    def __init__(self, term):
        self.payload = self.basic_payload
        self.payload['q'] = term

    def perform(self):
        r = requests.get(self.url, params=self.payload, headers=self.headers)
        
        for item in r.json()['data']['items']:
            print(item['title'])


args = {'q': 'home', 'safeSearch': 'none', 'orderby': 'relevance', 'max-results': 19, 'paid-content': 'false', 'v': 2, 'start-index': 1, 'alt': 'jsonc', 'category': 'Music'}

url = "https://gdata.youtube.com/feeds/api/videos"

headers = {'User-Agent': "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)"}

search = youtube_request('dotan')
search.perform()


#r = requests.get(url, params=args, headers=headers)
#respons = open('respons', 'w')
#respons.write(str(r.json()))
