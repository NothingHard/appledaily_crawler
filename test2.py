#coding: utf-8

import logging
import requests
from lxml import html as htmlparser

# __author__ = 'kevin'

logger = logging.getLogger(__name__)

def requests_test(url):
    session = requests.session()
    response = session.get(url)
    html = response.content.decode('utf-8', 'ignore')
    page = htmlparser.fromstring(html, base_url=url)
    #items = page.xpath(u"//select/option[@selected='']")
    items = page.xpath(u"//tr[@class='odd']")
    logger.warn("page count: %d" % (len(items)))
    # if (len(items)==0):
    #     logger.warn("page index not found")
    # else:    
    #     logger.warn("page index: %s" % (items[0].text))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(filename)s[line:%(lineno)d] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    requests_test("http://search.appledaily.com.tw/charity/projlist/Page/1")
    requests_test("http://search.appledaily.com.tw/charity/projlist/Page/162")
    requests_test("http://search.appledaily.com.tw/charity/projlist/Page/163")
    pass