#coding: utf-8
#import csv
# import codecs
# import datetime
# import time
# import os
# import urlparse
# import shutil
# import sys
# import urllib3
# import pycurl
# from StringIO import StringIO
# from lxml import etree
import requests
# from EmailHelper import EmailHelper
# from FileHelper import FileHelper
# from StrHelper import StrHelper
# import re
# from urldownloader import urldownloader

# __author__ = 'kevin'


class Crawler(object):
    def wget(self):
        os.system("wget "
                  "--page-requisites "  #get all the elements that compose the page (images, CSS and so on).
                  "--convert-links "  #convert links so that they work locally, off-line.
                  "--no-check-certificate "
                  "--adjust-extension "  #save HTML/CSS documents with proper extensions.
                  #"--save-headers "
                  #"--html-extension "
                  #"--include-directories=/fund-treatments/page, /profile "

                  "--span-hosts "  # go to foreign hosts when recursive.
                  #" --recursive "
                  "--level=1 "
                  "-e robots=off "  #execute command robotos=off as if it was part of .wgetrc file. This turns off the robot exclusion which means you ignore robots.txt and the robot meta tags (you should know the implications this comes with, take care).
                  "--follow-tags=img,script,link "
                  "--accept=jpg,html,css "
                  #"--server-response "
                  #"--timestamping "             #don't re-retrieve files unless newer than local.
                  #"https://watsi.org/fund-treatments")
                  "https://watsi.org/profile/99b89bdcc66f-malaysia")

    def curl(self):
        #http://blog.wanthings.com/archives/239
        c = pycurl.Curl()
        c.setopt(pycurl.URL, "https://watsi.org/profile/99b89bdcc66f-malaysia")

        b = StringIO()
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.MAXREDIRS, 5)
        # c.setopt(pycurl.HEADER, True)
        # c.setopt(c.HTTPHEADER, ["Content-Type: application/x-www-form-urlencoded","X-Requested-With:XMLHttpRequest","Cookie:"+set_cookie[0]])
        # 模擬瀏覽器
        #c.setopt(pycurl.USERAGENT, "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)")
        # c.setopt(pycurl.AUTOREFERER,1)
        # c.setopt(c.REFERER, url)
        c.perform()
        statusCode = c.getinfo(c.HTTP_CODE)
        html = b.getvalue()
        #print html
        # fh = open("file.html", "w")
        # fh.write(html)
        # fh.close()


def urllib3_run():
    #創建連接特定主機的連接池
    http_pool = urllib3.HTTPSConnectionPool('watsi.org')  #HTTPS
    #獲取開始時間
    strStart = time.strftime('%X %x %Z')
    for i in range(2, 3, 1):
        print i
        #組合URL字符串
        url = 'https://watsi.org/fund-treatments/page/%d' % i
        print url
        #開始同步獲取內容
        r = http_pool.urlopen('GET', url, redirect=True)
        if (r.status == 200):
            #print r.status, r.headers, len(r.data)
            #print r.data
            html = r.data.decode('utf-8', 'ignore')
            page = etree.HTML(html)
            nodes = page.xpath(u"//a[text()='Next ›']")
            print nodes[0].attrib['asdasdasd']
            urlNextPage = urlparse.urljoin(url, nodes[0].attrib['href']) if (len(nodes) > 0) else None
            print urlNextPage
        else:
            print r.status, r.headers, len(r.data)

    #打印時間
    print 'start time : ', strStart
    print 'end time : ', time.strftime('%X %x %Z')


import logging

logging.basicConfig(level=logging.INFO)


def moveWatsiFiles(dir):
    files = os.listdir(dir)
    for file in files:
        name, ext = os.path.splitext(file)
        if (ext != None and ext.lower() == ".txt"):
            newDir = os.path.join(os.path.join(dir, name[-1:]), name)
            if (not os.path.isdir(newDir)):
                os.makedirs(newDir)
            shutil.move(os.path.join(dir, file), os.path.join(newDir, "data" + ext))
            # if(os.path.isfile(os.path.join(newDir, "data.txt"))):
            #     file = open(os.path.join(dir, detailFileName), "wb")
            #             csvwriter = csv.writer(file)


def textTocsv(dir):
    paths = os.listdir(dir)
    for path in paths:
        if (os.path.isfile(os.path.join(dir, path))):
            name, ext = os.path.splitext(path)
            if (ext != None and ext.lower() == ".txt"):
                fullpath = os.path.join(dir, path)
                srcFile = open(os.path.join(dir, path), "r")
                dstFile = open(os.path.join(dir, name + ".csv"), "wb")
                csvwriter = csv.writer(dstFile)
                lines = srcFile.read().splitlines()
                for line in lines:
                    line = line.rstrip('\r\n')
                    cols = line.split("\t")
                    if (line == ""):
                        continue
                    csvwriter.writerow(cols)
                dstFile.close()
                srcFile.close()
                #os.remove(os.path.join(dir, path))
        if (os.path.isdir(os.path.join(dir, path))):
            textTocsv(os.path.join(dir, path))


def regexTest(regex, filename):
    with codecs.open(filename, "r", 'utf-8') as file:
        text = file.read()
        list = regex.findall(text)
        print ("list len = %d" % len(list))
        for index, item in enumerate(list):
            print "%d: %s" % (index, item)


def get_attrib(node, name, default=None):
    if (node == None):
        return default
    return node.attrib[name] if name in node.attrib else default


def saveProfile(profileName, dir, reportUrl):
    reportSrcFileName = "reportSrcFileName.html"
    reportFileName = "report.txt"
    assetdir = os.path.join(dir, "files" + os.sep)
    if (not os.path.isdir(dir)):
        os.makedirs(dir)
    if (not os.path.isdir(assetdir)):
        os.makedirs(assetdir)

    #self.downloader.clear_cache()
    downloader = urldownloader()
    status, page = downloader.download_page(reportUrl,
                                            dir,
                                            assetdir,
                                            reportSrcFileName,
                                            css=True,
                                            javascript=False,
                                            image=True)
    if (page != None):
        reporter = None
        reportContent = ""
        #headers
        items = page.xpath(u"//*[@id='maincontent']//article/header/hgroup/*")
        for item in items:
            header = StrHelper.trim(item.text_content())
            print(header)
            if (header != None and header.startswith(profileName)):
                header = StrHelper.trim(header[len(profileName):])
            reportContent += header + os.linesep
            break
        reportContent += os.linesep
        #content
        reg = re.compile(ur"^基金會編號.*$", re.MULTILINE)
        regReporters = [  #re.compile(ur"[。：」\s]+(.{3,4})口述.?記者(.{3,4})(?:採訪整理)?$", re.MULTILINE),
                          re.compile(ur"[\u4e00-\u9fa5\s。：」]+(.{2,4})[口筆]述\s?.?\s?記者(.{2,4})(?:採訪整理)?$", re.MULTILINE),
                          #[\u4e00-\u9fa5] 英文字符之外的字符，包括中文漢字和全角標點
                          re.compile(ur"報導.攝影.(.{2,4})記者$", re.MULTILINE),
                          re.compile(ur"報導.攝影.(.{2,4})$", re.MULTILINE),
                          re.compile(ur"攝影.報導.(.{2,4})$", re.MULTILINE),
                          re.compile(ur"攝影.(.{2,4})$", re.MULTILINE),
                          re.compile(ur"報導.(.{2,4})$", re.MULTILINE),
                          re.compile(ur"報導.(.{2,4})$", re.MULTILINE),
                          re.compile(ur"記者(.{2,4})採訪整理$", re.MULTILINE),
                          re.compile(ur"^【(.{2,4})╱.{2,4}報導】", re.MULTILINE), ]

        for br in page.xpath(u"//div[@class='articulum']//br"):  #preserve <br> tags as \n
            br.tail = "\n" + br.tail if br.tail else "\n"
        items = page.xpath(u"//div[@class='articulum']/*")
        for item in items:
            tag = item.tag.lower()
            id = get_attrib(item, "id", None)
            # if (tag == "figure"): continue
            # if (tag == "iframe"): break
            if (id == "bcontent" or id == "bhead" or id == "introid"):
                FileHelper.saveTextToFile(os.path.join(dir, reportFileName), item.text_content())
                text = StrHelper.trim(item.text_content())
                if (text == None or text == ""): continue
                if (id != "bhead"):

                    for index, regReporter in enumerate(regReporters):
                        list = regReporter.findall(text)
                        if (len(list) == 1):
                            if (not isinstance(list[0], basestring)):
                                reporter = "/".join(list[0])
                            else:
                                reporter = list[0]
                            print(reporter)
                            text = StrHelper.trim(regReporter.sub('', text))
                            break
                    if (reporter):
                        aReporter = reporter
                    else:
                        print("error: parsing reporter: %s" % reportUrl)

                text = StrHelper.trim(reg.sub('', text))
                reportContent += text + os.linesep + os.linesep
        FileHelper.saveTextToFile(os.path.join(dir, reportFileName), reportContent)


def removeDupItems(path):
    try:
        srcFile = open(path, "rb")
        dstFile = open(path+"_new", "wb")
        csvwriter = csv.writer(dstFile)
        for row in csv.reader(srcFile):
            print(row[0])
    except Exception as ex:
        print(ex)

def removeBadWatsi(path):
    items = os.listdir(path)
    for item in items:
        dir = os.path.join(path, item)
        if(os.path.isdir(dir)):
            csvFilename = os.path.join(dir, "data.csv")
            if(os.path.isfile(csvFilename)):
                dirFound=None
                with open(csvFilename, "rb") as file:
                    csvreader = csv.reader(file)
                    for values in csvreader:
                        if(len(values)>1):
                            id = item
                            progress=values[1]
                            if(progress=='0'):
                                #print("%s %s %s " % (id, progress, dir))
                                pass
                            else:
                                dirFound=dir
                                #print("%s %s %s " % (id, progress, dir))
                                pass
                        break
                if(dirFound!=None):
                    shutil.rmtree(dirFound)
            else:
                if(len(item)!=1):
                    print("%s: csv not found" % dir)
                removeBadWatsi(dir)
    pass


def reformatCsv(path):
    items = os.listdir(path)
    for item in items:
        dir = os.path.join(path, item)
        if(os.path.isdir(dir)):
            csvFilename = os.path.join(dir, "data.csv")
            if(os.path.isfile(csvFilename)):
                allrows=[]
                with open(csvFilename, "rb") as file:
                    csvreader = csv.reader(file)
                    lineno=0
                    for values in csvreader:
                        lineno+=1
                        if(len(values)==5):
                            id = item
                            timestamp=values[0]
                            progress=values[1]
                            raised=values[2]
                            togo=values[3]
                            donors=values[4]
                            for index in range(2,5):
                                #print(values[index])
                                value = values[index]
                                newValue = StrHelper.strToValue(value)
                                if(value!=newValue):
                                    values[index]=newValue
                                    print("error: invalid number value %s in %s:%d" % (value, csvFilename, lineno))
                            allrows.append(values)
                        else:
                            print("error: invalid col count in %s:%d" % (csvFilename, lineno))
                with open(csvFilename, "wb") as file:
                    csvwriter = csv.writer(file)
                    for values in allrows:
                        csvwriter.writerow(values)
            else:
                reformatCsv(dir)
    pass

def requests_test():
    session = requests.session()
    response = self.session.get("http://search.appledaily.com.tw/charity/projlist/Page/162")
    response = self.session.get("http://search.appledaily.com.tw/charity/projlist/Page/163")



if __name__ == '__main__':
    # #url = "http://www.appledaily.com.tw/appledaily/article/headline/20140321/35713641"
    # url = "http://www.appledaily.com.tw/appledaily/article/headline/20140321/35713641?aaa=bbb#ccc"
    # parser = urlparse.urlparse(url)
    # response = urllib3.connection_from_url(url).urlopen('GET', url)
    # #response = urllib3.connection_from_url(url).request('GET', parser.path)
    # html = response.data
    # print html
    #
    # # response = requests.get(url)
    # # response = requests.get("http://www.appledaily.com.tw/appledaily/article/headline/20140320/35710979")
    #
    # session = requests.Session()
    # response = session.get(url)
    # response = session.get("http://www.appledaily.com.tw/appledaily/article/headline/20140320/35710979")
    # html = response.content
    # print html

    #EmailHelper.send("test", "hello!!!")


    #moveWatsiFiles("G:\\Tmp\\1\\2\\3\\profiles")
    #textTocsv("G:\\Tmp\\1\\2\\3\\profiles")

    #moveWatsiFiles(sys.argv[1])
    #textTocsv(sys.argv[1])

    #regexTest(re.compile(ur"報導.攝影.(.*)$", re.MULTILINE), "G:\\Tmp\\RegexSample.txt")

    #saveProfile("A2412", "G:\\tmp\\", "http://www.appledaily.com.tw/appledaily/article/headline/20110309/33233651")


    #removeDupItems("V:\\crawler\\appledaily\\profiles\\overall.csv")

    #xxx=u"中文"

    #removeBadWatsi("G:\\Tmp\\1\\2\\3\\profiles")
    #removeBadWatsi("V:\\crawler\\watsi\\profiles")

    #reformatCsv("G:\\Tmp\\1\\2\\3\\profiles")
    #reformatCsv("V:\\crawler\\watsi\\profiles")
    requests_test()
    pass