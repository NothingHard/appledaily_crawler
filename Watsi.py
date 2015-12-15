#coding: utf-8
import csv
import datetime
import time
import os
import logging
import urlparse
import re

#from lxml import etree
from lxml import html as htmlparser
#from urlparse import urlparse
import ast
from CrawlerBase import CrawlerBase

from tendo import singleton
from LogHelper import LogHelper
from OverallEntryBase import OverallEntryBase

me = singleton.SingleInstance()  # will sys.exit(-1) if other instance is running

import sys

reload(sys)
sys.setdefaultencoding("utf8")

#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger(__name__)
#log = Log(logger)

profileHtmlSrcFilename = 'index.html'


class OverallEntry(OverallEntryBase):
    def __init__(self):
        super(OverallEntry, self).__init__()
        self.url = None


class Watsi(CrawlerBase):
    cache_key_id = "id"
    cache_key_progress = "progress"
    cache_key_raised = "raised"
    cache_key_togo = "togo"
    cache_key_donors = "donors"

    def __init__(self):
        super(Watsi, self).__init__()
        self.dictPatientInfos = {}
        self.patientInfosFile = None
        self.patientInfosFilename = os.path.join(self.outputDir, 'patients.cache')
        self.loadPatientInfos()

    def cache_profile_detailsWithDict(self, dict):
        if (self.patientInfosFile == None):
            self.patientInfosFile = open(self.patientInfosFilename, "a")
        self.patientInfosFile.write(str(dict))
        self.patientInfosFile.write(os.linesep)
        self.patientInfosFile.flush()


    def cache_profile_details(self, id, progress, raised, togo, donors):
        if (id in self.dictPatientInfos):
            entry = self.dictPatientInfos[id]
        else:
            entry = {}
            self.dictPatientInfos[id] = entry
        entry[self.cache_key_id] = id
        entry[self.cache_key_progress] = progress
        entry[self.cache_key_raised] = raised
        entry[self.cache_key_togo] = togo
        entry[self.cache_key_donors] = donors
        self.cache_profile_detailsWithDict(entry)

    def getPrevProgressById(self, id):
        if (id in self.dictPatientInfos):
            entry = self.dictPatientInfos[id]
            return entry[self.cache_key_progress] if self.cache_key_progress in entry else None
        else:
            return None


    def loadPatientInfos(self):
        if (os.path.isfile(self.patientInfosFilename)):
            file = None
            try:
                file = open(self.patientInfosFilename, "r")
                while True:
                    line = file.readline()
                    if not line: break
                    if line == "": continue
                    newEntry = ast.literal_eval(line)
                    if (isinstance(newEntry, dict) and "id" in newEntry):
                        id = newEntry[self.cache_key_id]
                        if (id in self.dictPatientInfos):
                            entry = self.dictPatientInfos[id]
                        else:
                            entry = {}
                            self.dictPatientInfos[id] = entry
                        for key in newEntry:
                            entry[key] = newEntry[key]
                self.logger.info("%d patient infos loaded" % len(self.dictPatientInfos))
            except Exception, ex:
                self.logger.exception(LogHelper.getExceptionMsg(ex, "Can't read cache file"))
            finally:
                if (file):
                    file.close()

        self.savePatientInfos()


    def savePatientInfos(self):
        if (self.patientInfosFile):
            self.patientInfosFile.close()
            self.patientInfosFile = None

        file = None
        try:
            file = open(self.patientInfosFilename, 'w').close()
        except Exception, ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "error: can't write cache file"))
        finally:
            if (file):
                file.close()
        if (len(self.dictPatientInfos) > 0):
            for key in self.dictPatientInfos:
                self.cache_profile_detailsWithDict(self.dictPatientInfos[key])
            self.logger.info("%d patient infos saved" % len(self.dictPatientInfos))


    def save_profile_details(self, filename, list):
        file = None
        try:
            file = open(filename, "ab")
            writer = csv.writer(file)
            writer.writerow(list)
            file.flush()
        except Exception as ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "unable to save file: %s" % (filename)))
        finally:
            if (file != None):
                file.close()

    # def save_profile_details(self, filename, list):
    #     file = None
    #     try:
    #         file = open(filename, mode='a')
    #         #file.write(u'\ufeff')  #codecs.BOM_UTF8
    #         file.write('\t'.join(list))
    #         file.write(os.linesep)
    #         file.flush()
    #     except Exception as ex:
    #         self.logger.exception(LogHelper.getExceptionMsg(ex, "unable to save file: %s\n\t%s" % (filename)))
    #     finally:
    #         if (file):
    #             file.close()

    def freeResource(self):
        super(Watsi, self).freeResource()
        if (self.patientInfosFile):
            self.patientInfosFile.close()

    def parsePages(self):
        try:
            pageIndex = 1
            #urlNextPage = 'https://watsi.org/fund-treatments/page/129'
            urlNextPage = 'https://watsi.org/fund-treatments/'
            while True:
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
                    #find next page's url
                    nodes = page.xpath(u"//a[text()='Next ›']")
                    urlNextPage = urlparse.urljoin(currentPage, nodes[0].attrib['href']) if (len(nodes) > 0) else None

                    items = page.xpath(u"//div[@class='profiles']/ul/li")
                    if (items):
                        for item in items:
                            id = item.attrib["id"]
                            node = self.find_element_by_xpath(item, u".//div/a")
                            url = self.get_attrib(node, "href", None)
                            urlProfile = urlparse.urljoin(currentPage, url) if url else None
                            node = self.find_element_by_xpath(item,
                                                              u".//*[@class='info-bar']")  #info-bar 會在 <p> or <div> 中
                            title = node.text if node != None else ""
                            node = self.find_element_by_xpath(item, u".//p[@class='profile-description']")
                            description = node.text if node != None else ""
                            node = self.find_element_by_xpath(item, u".//div[@class='cont']/a/img")
                            imgSrc = self.get_attrib(node, "src", "")

                            #Progress
                            node = self.find_element_by_xpath(item, u".//div[@class='meter orange nostripes']/span")
                            progressStr = self.get_attrib(node, "style", "")
                            list = re.findall(ur"[;^]*?\s*?width:\s*([,\d]*)", progressStr)
                            progress = None
                            if(len(list)==1):
                                progress = list[0]

                            #togo raised donors
                            togo = None
                            raised = None
                            donors = None

                            if(title=="The Universal Fund"):
                                continue
                            else:
                                list = re.findall(ur"\$?([,\d]*)\s*(.*?)\s*\|\s*([,\d]*)\s*(.*)", title)
                                if (len(list) == 1 and len(list[0]) == 4):
                                    values = list[0]
                                    if (values[1] != None and values[1].lower() == "raised"):
                                        raised = values[0]
                                        donors = values[2]
                                    elif (values[1] != None and values[1].lower() == "to go"):
                                        togo = values[0]
                                        donors = values[2]
                                    else:
                                        self.logger.error("invalid reg pattern for %s in page %s" % (title, currentPage))
                                        continue
                                else:
                                    self.logger.error("invalid reg pattern for %s in page %s" % (title, currentPage))
                                    continue

                            if (raised != None):
                                raised = re.sub(ur"[,$]", "", raised)
                            if (togo != None):
                                togo = re.sub(ur"[,$]", "", togo)
                            if (donors != None):
                                donors = re.sub(ur"[,$]", "", donors)

                            #Log.i("%s %s" %(id, progress))
                            #Log.i("%s %s" %(id, urlProfile))
                            # Log.i("%s %s" %(id, title))
                            # Log.i("\t%s" % description)
                            # Log.i("\t%s" % imgSrc)
                            outputDir = os.path.join(os.path.join(self.profileDir, id[-1:]), id)
                            if (progress == '0' and not (os.path.isdir(outputDir))):
                                os.makedirs(outputDir)
                            if not os.path.exists(outputDir):
                                continue
                            if (self.getPrevProgressById(id) != '100'):
                                self.parseProfile(id, urlProfile, outputDir, donors)
                            else:
                                self.ensureProfileDownloaded(id, urlProfile, outputDir)
                            self.saveOverallEntry(id, [id, urlProfile])
                            self.cache_profile_details(id, progress, raised, togo, donors)
                        self.logger.info("%d items found" % (len(items)))
                    if (not items):
                        self.logger.info("items not found")
                        break
                    if (len(items) == 0):
                        self.logger.info("items length == 0")
                        break
                    if (not urlNextPage):
                        self.logger.info("NextPage not found")
                        break
                    pageIndex += 1
            self.savePatientInfos()
            self.logger.info('done!')
        except Exception as ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "parsePages"))
        finally:
            pass

    def parseProfile(self, name, urlProfile, outputDir, donors):
        result = False
        try:
            self.logger.info('downloading profile %s...' % name)
            #filename = '%s.html' % datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
            status, page = self.downloader.download_page(urlProfile,
                                                         outputDir,
                                                         self.assetDir,
                                                         profileHtmlSrcFilename,
                                                         css=True,
                                                         javascript=True,
                                                         image=False)
            if (page == None):
                pass
            elif (status != 200):
                self.logger.warn("http response: %s %s" % (status, urlProfile))
            else:
                detailedFound = False
                progress = ""
                raised = ""
                togo = ""
                nodeDetailes = self.find_element_by_xpath(page, u'//div[@id="funding_details"]')
                #text = htmlparser.tostring(nodeDetailes, "innerHTML")
                text=nodeDetailes.text_content()
                if (text != None and text != ""):
                    text = text.lower()
                    list = re.findall(ur"([\d\.]+?)%\s*(.*?)\$([\d,]+)\s*(.*?)\s*?$", text)
                    if (len(list) == 1 and len(list[0]) == 4):
                        values = list[0]
                        if (values[1] != None and values[3] == "raised"):
                            progress = values[0]
                            raised = values[2]
                            detailedFound = True
                        elif (values[1] != None and values[3] == "to go"):
                            progress = values[0]
                            togo = values[2]
                            detailedFound = True
                    if(not detailedFound):
                        self.logger.error("invalid reg pattern for %s in profile %s" % (text, urlProfile))

                if (not detailedFound):
                    self.logger.error("profile %s details not found" % name)
                else:
                    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                    if (raised != None):
                        raised = re.sub(ur"[,$]", "", raised)
                    if (togo != None):
                        togo = re.sub(ur"[,$]", "", togo)
                    details = [timestamp, progress, raised, togo, donors]
                    self.logger.info("profile %s details: %s" % (name, str(details)))
                    #self.save_profile_details(os.path.join(outputDir, '%s.txt' % (name)), details)
                    self.save_profile_details(os.path.join(outputDir, 'data.csv'), details)
                    result = True
        except Exception as ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "Exception: %s: %s " % ("parseProfile", name)))
        finally:
            pass
        return result

    def ensureProfileDownloaded(self, id, urlProfile, outputDir):
        filename = os.path.join(outputDir, profileHtmlSrcFilename)
        if (os.path.isfile(filename)):
            return
        status, page = self.downloader.download_page(urlProfile,
                                                     outputDir,
                                                     self.assetDir,
                                                     profileHtmlSrcFilename,
                                                     css=True,
                                                     javascript=True,
                                                     image=False)


if __name__ == '__main__':
    crawler = Watsi()
    crawler.run()