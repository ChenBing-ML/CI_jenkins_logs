import requests
import json
import time
import pymongo
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from random import choice

client = pymongo.MongoClient('localhost', 27017)
mydb = client['spider_data']
lagou = mydb['Machine_Learning']

# ip_proxy=[line[:-1] for line in open('./ip_ok.txt')]
base_url = 'https://www.lagou.com/jobs/'
ua = UserAgent()
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(chrome_options=options)
cookie = open('cookies_lagou', 'r').read().splitlines()[0]
ip_proxy_api = open('ip_proxy_api_16yun').read().strip()
headers = {'cookie': cookie,
           'origin': "https://www.lagou.com",
           'x-anit-forge-code': "0",
           'accept-encoding': "gzip, deflate, br",
           'accept-language': "zh-CN,zh;q=0.8,",
           'user-agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
           'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
           'accept': "application/json, text/javascript, */*; q=0.01",
           'referer': "https://www.lagou.com/jobs/list_%E8%87%AA%E5%8A%A8%E9%A9%BE%E9%A9%B6?px=default&city=%E5%85%A8%E5%9B%BD",
           'x-requested-with': "XMLHttpRequest",
           'connection': "keep-alive",
           'x-anit-forge-token': "None"}
 

def get_detail_page(positionId):
    job_url = base_url + str(positionId) + '.html' 
    filter_element = '#job_detail > dd.job_bt > div'
    try:
        driver.get(job_url)
        elements = driver.find_element_by_css_selector(filter_element)
        result = BeautifulSoup(elements.get_attribute('innerHTML'), 'html.parser').text
    except Exception as e:
        result = ''
        print('************job_url=', job_url)
        print(e)
    finally:
        return(result)

 
def get_page(url, params):
    headers['user-agent'] = choice(ua.data_browsers[choice(list(ua.data_browsers.keys()))])
    global ip_proxy
    ip_proxy = requests.get(url=ip_proxy_api, headers={'user-agent': headers['user-agent']}).text.split('\r\n')
    html = requests.post(url, data=params, headers=headers, proxies={'https': choice(ip_proxy)})
    # proxies={'https': choice(ip_proxy)}
    json_data = json.loads(html.text)
    print(json_data)
    total_count = json_data['content']['positionResult']['totalCount']
    page_number = int(total_count/15) if int(total_count/15)<100 else 100
    print("page_number=", page_number)
    time.sleep(10)
    get_info(url,page_number)
    
        
 
def get_info(url,page):
    for pn in range(46,page+1):
        params={
            'first':'true',
            'pn':str(pn),
            'kd':'机器学习'
        }
        try:
            for _ in range(5):
                try:
                    headers['user-agent'] = choice(ua.data_browsers[choice(list(ua.data_browsers.keys()))])
                    time.sleep(5)
                    global ip_proxy
                    ip_proxy = requests.get(url=ip_proxy_api, headers={'user-agent': headers['user-agent']}).text.split('\r\n')
                    html = requests.post(url, data=params, headers=headers, proxies={'https': choice(ip_proxy)})
                    #,proxies={'https': choice(ip_proxy)}
                    global json_data
                    json_data = json.loads(html.text)
                    if json_data['success'] == True:
                        break
                except Exception as e:
                    print('第{}页有问题:'.format(pn), e)
                    time.sleep(10)
            results = json_data['content']['positionResult']['result']
            num = 1
            for result in results:
                print('爬到第{}页第{}个了......'.format(pn, num))
                num += 1
                print('companyFullName', result['companyFullName'])
                infos = {
                    'businessZones':result['businessZones'],
                    'city': result['city'],
                    'companyFullName': result['companyFullName'],
                    'companyLabelList': result['companyLabelList'],
                    'companySize': result['companySize'],
                    'district': result['district'],
                    'education': result['education'],
                    'financeStage': result['financeStage'],
                    'firstType': result['firstType'],
                    'formatCreateTime': result['formatCreateTime'],
                    'gradeDescription': result['gradeDescription'],
                    'imState': result['imState'],
                    'industryField': result['industryField'],
                    'positionAdvantage': result['positionAdvantage'],
                    'salary': result['salary'],
                    'workYear': result['workYear'],
                }
                job_detail = get_detail_page(result['positionId'])
                infos['job_detail'] = job_detail
                lagou.insert_one(infos)
                print('insert data to mongodb...')
                time.sleep(1)
        except Exception as e:
            print('确确实实出现了异常：', e)
            pass
 
if __name__ == '__main__':
    url = 'https://www.lagou.com/jobs/positionAjax.json'
    params = {
        'first': 'true',
        'pn': '1',
        'kd': '机器学习'
    }

    try:
        get_page(url,params)
    except Exception as e:
        print(e)
    finally:
        driver.close()
        driver.quit()

