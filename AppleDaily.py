#coding: utf-8
import datetime
import time
import os
import sys
import getopt
import logging
import urlparse
import re
import csv

import urllib3
#from lxml import etree
from lxml import html as htmlparser
#from urlparse import urlparse
import ast
from CrawlerBase import CrawlerBase
from FileHelper import FileHelper
from LogHelper import LogHelper
from OverallEntryBase import OverallEntryBase
from StrHelper import StrHelper
import urldownloader

from tendo import singleton

me = singleton.SingleInstance()  # will sys.exit(-1) if other instance is running

import sys

reload(sys)
sys.setdefaultencoding("utf8")

#logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)
# log = Log(logger)

reportSrcFileName = 'report.html'
reportFileName = 'report.txt'
detailSrcFileName = 'detail.html'
detailFileName = 'detail.txt'
#metadataFileName = 'metadata.txt'


class OverallEntry(OverallEntryBase):
    def __init__(self):
        super(OverallEntry, self).__init__()
        self.begindate = None
        self.enddate = None
        self.total = 0
        self.doners = 0
        self.title = None
        self.reporter = None


class AppleDaily(CrawlerBase):
    cache_key_id = "id"
    cache_key_progress = "progress"
    cache_key_raised = "raised"
    cache_key_togo = "togo"
    cache_key_donors = "donors"

    def __init__(self):
        super(AppleDaily, self).__init__()


    def freeResource(self):
        super(AppleDaily, self).freeResource()

    def parsePages(self):
        try:
            pageIndex = 1
            while True:
                urlNextPage = 'http://search.appledaily.com.tw/charity/projlist/Page/%d' % pageIndex
                self.logger.info('downloading page %d...' % pageIndex)
                currentPage = urlNextPage
                status, page = self.downloader.download_page(currentPage,
                                                             self.htmlDir,
                                                             self.assetDir,
                                                             'page%05d.html' % (pageIndex),
                                                             css=False,
                                                             javascript=False,
                                                             image=False)

                if (page == None):
                    self.logger.warn("error: downloading page %d" % (pageIndex))
                    break
                elif (status != 200):
                    self.logger.warn("http response: %s %s" % (status, currentPage))
                    break
                else:
                    self.logger.info('parsing page %d...' % pageIndex)

                    items = page.xpath(u"//tr[@class='odd']")
                    row = 0
                    if (items):
                        for item in items:
                            nodes = item.xpath(u".//td")
                            if (len(nodes) == 6):
                                reportUrl = None
                                detailUrl = None
                                title = None
                                row += 1
                                id = nodes[0].text
                                node = nodes[1].xpath(u".//a")
                                if len(node) > 0:
                                    title = node[0].text
                                    reportUrl = urlparse.urljoin(currentPage, self.get_attrib(node[0], "href", None))
                                else:
                                    self.logger.warn("title not found")
                                date = nodes[2].text
                                status = str(nodes[3].text_content())
                                amount = nodes[4].text
                                node = nodes[5].xpath(u".//a")
                                if len(node) > 0:
                                    detailUrl = urlparse.urljoin(currentPage, self.get_attrib(node[0], "href", None))
                                else:
                                    self.logger.warn("detail not found")

                                if (title == None):
                                    self.logger.warn("title not found")
                                if (title == None or reportUrl == None or detailUrl == None):
                                    self.logger.warn("parse error!!!")
                                if (status == u"已結案"):
                                    dir = os.path.join(self.profileDir, id[-1:] + os.sep + id + os.sep)
                                    if (not self.getIsProfileSaved(dir)):
                                        #self.logger.warn("saving profile: page %d, id %s" % (pageIndex, id))
                                        overallEntry = OverallEntry()
                                        overallEntry.id = id
                                        overallEntry.title = StrHelper.trim(title)
                                        overallEntry.total = amount
                                        overallEntry.begindate = date
                                        self.logger.info("saving profile %s" % id)
                                        self.saveProfile(id, dir, reportUrl, detailUrl, overallEntry)
                                        self.saveOverallEntry(overallEntry.id, [overallEntry.id,
                                                                                overallEntry.begindate,
                                                                                overallEntry.enddate,
                                                                                overallEntry.total,
                                                                                overallEntry.doners,
                                                                                overallEntry.title,
                                                                                overallEntry.reporter])
                                    self.saveUrls(dir, reportUrl, detailUrl)
                                    #self.saveMetadata(dir, title, date, amount)
                                elif (status == u"未結案"):
                                    pass
                                else:
                                    self.logger.warn("unknown status")

                    self.logger.info("%d items found" % (row))
                    if (row == 0):
                        break
                    if (not items):
                        self.logger.info("items not found")
                        break
                    if (len(items) == 0):
                        self.logger.info("items length == 0")
                        break
                    pageIndex += 1
            self.logger.info('done!')
        except Exception as ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "parsePages"))
        finally:
            pass

    def getIsProfileSaved(self, dir):
        if (not os.path.isdir(dir)):
            return False
        files = [detailFileName, reportSrcFileName, detailSrcFileName]
        for file in files:
            filename = os.path.join(dir, file)
            if (not os.path.isfile(filename)):
                return False

        return True

    def saveProfile(self, profileName, dir, reportUrl, detailUrl, overallEntry):
        assetdir = os.path.join(dir, "files" + os.sep)
        if (not os.path.isdir(dir)):
            os.makedirs(dir)
        if (not os.path.isdir(assetdir)):
            os.makedirs(assetdir)

        #self.downloader.clear_cache()
        status, page = self.downloader.download_page(reportUrl,
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
                if (header != None and header.startswith(profileName)):
                    header = StrHelper.trim(header[len(profileName):])
                reportContent += header + os.linesep
                break
            reportContent += os.linesep
            #content
            reg = re.compile(ur"^基金會編號.*$", re.MULTILINE)
            allsymbols = ur"　，、。．？！～＄％＠＆＃＊‧；︰…‥﹐﹒˙·﹔﹕‘’“”〝〞‵′〃├─┼┴┬┤┌┐╞═╪╡│▕└┘╭╮╰╯╔╦╗╠═╬╣╓╥╖╒╤╕║╚╩╝╟╫╢╙╨╜╞╪╡╘╧╛﹣﹦≡｜∣∥–︱—︳╴¯￣﹉﹊﹍﹎﹋﹌﹏︴﹨∕╲╱＼／↑↓←→↖↗↙↘〔〕【】﹝﹞〈〉﹙﹚《》（）｛｝﹛﹜『』「」＜＞≦≧﹤﹥︵︶︷︸︹︺︻︼︽︾︿﹀∩∪﹁﹂﹃﹄"
            regReporters = [  #re.compile(ur"[。：」\s]+(.{3,4})口述.?記者(.{3,4})(?:採訪整理)?$", re.MULTILINE),
                              re.compile(allsymbols + ur"[\s]+(.{2,4})[口筆]述\s?.?\s?記者(.{2,4})(?:採訪整理)?$", re.MULTILINE),
                              #[\u4e00-\u9fa5] 英文字符之外的字符，包括中文漢字和全角標點
                              re.compile(ur"報導.攝影.(.{2,4})記者$", re.MULTILINE),
                              re.compile(ur"報導.攝影.(.{2,4})$", re.MULTILINE),
                              re.compile(ur"攝影.報導.(.{2,4})$", re.MULTILINE),
                              re.compile(ur"攝影.(.{2,4})$", re.MULTILINE),
                              re.compile(ur"報導.(.{2,4})$", re.MULTILINE),
                              re.compile(ur"報導.(.{2,4})$", re.MULTILINE),
                              re.compile(ur"記者(.{2,4})採訪整理$", re.MULTILINE),
                              re.compile(ur"^【(.{2,4})╱.{2,4}報導】", re.MULTILINE), ]

            #preserve <br> tags as \n
            for br in page.xpath(u"//div[@class='articulum']//br"):
                br.tail = "\n" + br.tail if br.tail else "\n"

            items = page.xpath(u"//div[@class='articulum']/*")
            for item in items:
                tag = item.tag.lower()
                id = self.get_attrib(item, "id", None)
                # if (tag == "figure"): continue
                # if (tag == "iframe"): break
                if (id == "bcontent" or id == "bhead" or id == "introid"):
                    text = StrHelper.trim(item.text_content())
                    if (text == None or text == ""): continue
                    if (id != "bhead"):
                        for regReporter in regReporters:
                            list = regReporter.findall(text)
                            if (len(list) == 1):
                                if (not isinstance(list[0], basestring)):
                                    reporter = "/".join(list[0])
                                else:
                                    reporter = list[0]
                                text = StrHelper.trim(regReporter.sub('', text))
                                break
                        if (reporter):
                            overallEntry.reporter = reporter
                        else:
                            self.logger.warn("error: parsing reporter: %s" % reportUrl)

                    text = StrHelper.trim(reg.sub('', text))
                    reportContent += text + os.linesep + os.linesep
            FileHelper.saveToFile(os.path.join(dir, reportFileName), reportContent)

        status, page = self.downloader.download_page(detailUrl,
                                                     dir,
                                                     assetdir,
                                                     detailSrcFileName,
                                                     css=True,
                                                     javascript=False,
                                                     image=True)
        if (page != None):
            items = page.xpath(u"//div[@id='charitysidebox3'][1]/div[@id='inquiry3']/table//tr")
            maxDate = None
            if (len(items) > 0):
                file = None
                try:
                    file = open(os.path.join(dir, detailFileName), "wb")
                    csvwriter = csv.writer(file)
                    for index, item in enumerate(items):
                        if (index > 1):
                            cols = item.xpath(u".//td")
                            if (len(cols) == 4):
                                no = StrHelper.trim(cols[0].text)
                                name = StrHelper.trim(cols[1].text)
                                amount = StrHelper.trim(cols[2].text)
                                dateStr = StrHelper.trim(cols[3].text)
                                try:
                                    date = datetime.datetime.strptime(dateStr, "%Y/%m/%d")
                                    if (maxDate == None or date > maxDate):
                                        maxDate = date
                                except Exception as ex:
                                    self.logger.warn("error date format:%s in %s" % (dateStr, detailUrl))
                                csvwriter.writerow([no, dateStr, amount, name])
                    overallEntry.enddate = maxDate.strftime("%Y/%m/%d") if maxDate != None else ""
                    overallEntry.doners = len(items) - 2
                except Exception as ex:
                    self.logger.exception(LogHelper.getExceptionMsg(ex, "error paring detail.html"))
                finally:
                    if (file):
                        file.close()


    # def saveMetadata(self, dir, title, date, amount):
    #     filename = os.path.join(dir, metadataFileName)
    #     self.saveToFile(filename, "\t".join([date, amount, title]))

    def saveToFile(self, filename, data):
        file = None
        try:
            file = open(filename, mode='wb')
            file.write(data)
        except Exception as ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "unable to save file: %s" % filename))
        finally:
            if (file):
                file.close()
        pass

    # def loadOverallEntries(self):
    #     filename = os.path.join(self.profileDir, overallFileName)
    #     if (os.path.isfile(filename)):
    #         with open(filename, 'rb') as csvfile:
    #             for row in csv.reader(csvfile):
    #                 if (len(row) > 0):
    #                     self.overallEntries[row[0]] = True
    #
    # def saveOverallEntry(self, overallEntry):
    #     if (overallEntry.id in self.overallEntries):
    #         return
    #     self.overallEntries[overallEntry.id] = True
    #     #self.logger.warn("saveOverallEntry -- overallEntry.title: %s" % overallEntry.title)
    #     self.overallEntriesWriter.writerow([overallEntry.id,
    #                                         overallEntry.begindate,
    #                                         overallEntry.enddate,
    #                                         overallEntry.total,
    #                                         overallEntry.doners,
    #                                         overallEntry.title,
    #                                         overallEntry.reporter])
    #     self.overallEntriesFile.flush()

    def saveUrls(self, dir, reportUrl, detailUrl):
        filename = os.path.join(dir, "urls.txt")
        if (not os.path.isfile(filename)):
            FileHelper.saveToFile(filename, '%s\r\b%s' % (reportUrl, detailUrl))
            #with open(os.path.join(dir, "urls.txt"), "w")


if __name__ == '__main__':
    crawler = AppleDaily()
    crawler.run()
