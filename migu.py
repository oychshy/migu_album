import requests
import re
import urllib.parse


def search(key_word:str,page_number,page_size):
    switch = "{\"song\":1,\"album\":0,\"singer\":0,\"tagSong\":0,\"mvSong\":0,\"songlist\":0,\"bestShow\":1}"
    url = f'http://pd.musicapp.migu.cn/MIGUM2.0/v1.0/content/search_all.do?ua=Android_migu&version=5.0.1&pageNo={page_number}&pageSize={page_size}&text={key_word}&searchSwitch={switch}'
    print("url ", url)
    data = requests.get(url, verify=False).json()
    print("response: ", data)

    code = int(data["code"])
    if code != 0:
        msg = 'code:' + str(code)
        return msg

    if data["songResultData"]["totalCount"] == None:
        return "not result"

    total_count = str(data["songResultData"]["totalCount"])
    print("total_count: ", total_count)
    songs = []
    for song_info in data["songResultData"]["result"]:
        singers = []
        for singer in song_info["singers"]:
            singers.append({
                'id': str(singer["id"]),
                'name': str(singer["name"]),
            })

        albums = []

        if song_info.get('albums'):
            for a in song_info["albums"]:
                albums.append({
                    'id': str(a["id"]),
                    'name': str(a["name"]),
                })

        image_items = song_info["imgItems"]
        image_url = ''
        if len(image_items) > 0:
            image_url = str(image_items[0]["img"])

        download_url = getUrl(song_info["id"])
        if not download_url:
            download_url = '未找到'

        song = {
            'id': str(song_info["id"]),
            'name': str(song_info["name"]),
            'image_url':image_url,
            'download_url':download_url,
            'singers':singers,
            'albums':albums,
        }
        songs.append(song)
    print(songs)


def extract_submatch(expression, input_string):
    try:
        pattern = re.compile(expression)
    except re.error as e:
        return "", str(e)

    match = pattern.findall(input_string)

    if len(match) > 1 or len(match[0]) == 0:
        return "", "should match one only"
    else:
        return match[0], None

def getUrl(sid):
    target_url = f'https://app.c.nf.migu.cn/MIGUM2.0/strategy/listen-url/v2.2?netType=01&resourceType=E&songId={str(sid)}&toneFlag=PQ'
    headers = {
        "Origin" : "http://music.migu.cn/",
        "Referer" : "http://m.music.migu.cn/v3/",
        "aversionid" : None,
        "channel" : "0146921",
    }
    ret = requests.get(target_url,headers=headers,verify=False).json()
    data = ret['data']

    url = data.get('url')
    if url == None:
        print('error')
        return False

    mp3_index = url.rfind('.mp3')
    if mp3_index != -1:
        mp3_url = url[:mp3_index + 4]
    else:
        print("URL 中没有找到")
        return False

    parts = mp3_url.split('/')
    flac_list = list(filter(lambda item: item and item.strip(), parts))
    hq_list = list(filter(lambda item: item and item.strip(), parts))

    flac_list[-3] = '%E6%AD%8C%E6%9B%B2%E4%B8%8B%E8%BD%BD'
    flac_list[-2] = 'flac'
    sname = flac_list[-1].rsplit('.', 1)[0]
    flac_list[-1] = sname+'.flac'

    flac_url = ''
    for index, value in enumerate(flac_list):
        if index == 0:
            flac_url = flac_url + value + '//'
        elif index == len(flac_list) - 1:  # 判断是否为最后一位元素
            flac_url = flac_url + value
        else:
            flac_url = flac_url + value + '/'

    checkUrl = check_url_exists(flac_url)
    hq_url = ''
    if not checkUrl:
        hq_list[-2] = 'MP3_320_16_Stero'
        for index, value in enumerate(hq_list):
            if index == 0:
                hq_url = hq_url + value + '//'
            elif index == len(hq_list) - 1:  # 判断是否为最后一位元素
                hq_url = hq_url + value
            else:
                hq_url = hq_url + value + '/'
        return hq_url
    else:
        return flac_url


def new(AlbumId):
    fullUrl = "https://app.c.nf.migu.cn/MIGUM2.0/v1.0/content/resourceinfo.do?needSimple=01&resourceId="+str(AlbumId)+"&resourceType=2003";
    headers = {
        'User-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_4_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.11(0x17000b21) NetType/4G Language/zh_CN',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Host': 'app.c.nf.migu.cn',
        'Content-Type': 'application/json;charset=utf-8',
    }
    data = requests.get(fullUrl,headers=headers,verify=False).json()
    print(data)
    if data['resource'][0] and data['resource'][0]['songItems']:
        for item in data['resource'][0]['songItems']:
            singer = item['singer']
            album = item['album']
            songName = item['songName']
            newRateFormats = item['newRateFormats']
            urls = []
            for formatItem in newRateFormats:
                urlInfo = {}
                formatType = formatItem['formatType']
                urlInfo['formatType'] = formatType
                songUrl = None
                if 'url' in formatItem:
                    url = formatItem['url']
                else:
                    url = formatItem['androidUrl']
                result, error = extract_submatch('ftp:\/\/[^/]+\/(.*)', url)
                if error:
                    print("Error:", error)
                else:
                    result = urllib.parse.quote(result)
                    songUrl = "https://freetyst.nf.migu.cn/" + result
                    songUrl = songUrl.replace("+", "%2B")
                urlInfo['songUrl'] = songUrl
                urls.append(urlInfo)

            print({
                'singer':singer,
                'songName':songName,
                'album':album,
                'urls':urls
            })

def check_url_exists(url):
    try:
        response = requests.head(url)
        if response.status_code == 200:
            # print(f"资源存在: {url}")
            return True
        else:
            # print(f"资源不存在,状态码: {response.status_code} - {url}")
            return False
    except requests.exceptions.RequestException as e:
        # print(f"请求错误: {e} - {url}")
        return False



if __name__ == '__main__':
    new(1000019974)
    # search("许巍", 1, 10)
    # getUrl(1000020399)