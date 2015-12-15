#coding: utf-8
from shutil import copyfile
from FileHelper import FileHelper
from LogHelper import LogHelper

__author__ = 'kevin'
import datetime
import time
import os
import sys
import getopt
import logging
import urlparse
import re


import urllib
import urllib2
#import urllib3
import requests
#from lxml import etree
from lxml import html as htmlparser
import gzip
from StringIO import StringIO

class AssetEntry:
    def __init__(self, path, filename):
        self.path=path
        self.filename=filename

class urldownloader:
    def __init__(self):
        #logging.basicConfig(level=logging.WARN)
        self.logger = logging.getLogger(LogHelper.LoggerName)
        self.dictPools = {}
        self.dictAssetFiles = {}
        self.assetFileIndex = 0
        self.session = requests.session()

    # def get_http_pool(self, url):
    #     return urllib3.connection_from_url(url)

    # def get_http_pool(self, url):
    #     parser = urlparse.urlparse(url)
    #     scheme = str(parser.scheme).lower()
    #     key = scheme + "://" + parser.netloc
    #     if(key in self.dictPools):
    #         return self.dictPools[key]
    #
    #     if (scheme == "http"):
    #         http_pool = urllib3.HTTPConnectionPool(parser.netloc)
    #     elif (scheme == "https"):
    #         http_pool = urllib3.HTTPSConnectionPool(parser.netloc)
    #     else:
    #         http_pool = None
    #     if(http_pool!=None):
    #         self.dictPools[key]=http_pool
    #     return http_pool

    def get_attrib(self, node, name, default=None):
        if (node == None):
            return default
        return node.attrib[name] if name in node.attrib else default

    def set_attrib(self, node, name, value):
        if (node == None):
            return
        node.attrib[name] = value

    def saveToFile(self, filename, data):
        file = None
        try:
            file = open(filename, mode='wb')
            file.write(data)
        except Exception as ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "unable to save file: %s" % (filename)))
        finally:
            if (file):
                file.close()

    # def saveResponseFile(self, filename, response):
    #     file = None
    #     try:
    #         file = open(filename, mode='w')
    #         while True:
    #             data = response.read(102400)
    #             if data is None:
    #                 break
    #             file.write(data)
    #     except Exception as ex:
    #         self.logger.error("unable to save file: %s\n\t%s" % (filename, str(ex)))
    #     finally:
    #         if (file):
    #             file.close()

    def saveTextToFile(self, filename, data):
        file = None
        try:
            #file = codecs.open(filename, mode='w', encoding="utf-8")
            #file = codecs.open(filename, mode='wb')
            file = open(filename, mode='w')
            #file.write(u'\ufeff')  #codecs.BOM_UTF8
            file.write(data)
        except Exception as ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "unable to save file: %s" % filename))
        finally:
            if (file):
                file.close()

    # def getNextAssetFilename(self, ext=""):
    #     self.assetFileIndex += 1
    #     return "file%d%s" % (self.assetFileIndex, ext)
    #     #return os.path.join(self.assetDir, "file%d" % (self.assetFileIndex))


    def saveAssetFile(self, url, assetDir):
        result=False
        response = None
        if (url in self.dictAssetFiles):
            assetEntry = self.dictAssetFiles[url]
            if(assetEntry.path!=assetDir):
                copyfile(os.path.join(assetEntry.path, assetEntry.filename), os.path.join(assetDir, assetEntry.filename))
            return
        try:
            response = self.session.get(url)
        except Exception, ex:
            self.logger.warn("url download error: %s" % url)
            self.logger.warn("\t %s" % str(ex))


        #parser = urlparse.urlparse(url)
        #name, ext = os.path.splitext(parser.path)
        #assetFilename = self.getNextAssetFilename(ext)
        assetFilename = FileHelper.getValidFilename(url)
        filename = os.path.join(assetDir, assetFilename)
        if (response != None and response.status_code == 200):
            #self.saveTextToFile(filename, data)
            self.saveToFile(filename, response.content)
            result=True
        else:
            self.saveTextToFile(filename, "")
            pass
        self.dictAssetFiles[url] = AssetEntry(assetDir, assetFilename)
        #self.dictAssetFiles[url] = "file:" + urllib.pathname2url(filename)
        return result

    def clear_cache(self):
        self.dictAssetFiles={}

    def download_related_files(self, page, xpath, attrib, pageDir, assetDir, baseurl=""):
        items = page.xpath(xpath)
        for item in items:
            url = self.get_attrib(item, attrib, None)
            if (url == None or url == ""):
                continue
            url = urlparse.urljoin(baseurl, url)
            self.saveAssetFile(url, assetDir)
            if(url in self.dictAssetFiles):
                assetEntry = self.dictAssetFiles[url]
                relPath = urllib.pathname2url(os.path.relpath(os.path.join(assetDir, assetEntry.filename), pageDir))
                self.set_attrib(item, attrib, relPath)


    def download_page(self, url, outDir, assetDir, filename, css=False, javascript=False, image=False):
        page = None
        #response = self.get_http_pool(url).request('GET', url, headers=headers)
        try:
            response = self.session.get(url)
        except requests.exceptions.ConnectionError as connectionError:
            return -1, None
        except Exception as ex:
            self.logger.exception(LogHelper.getExceptionMsg(ex, "exception: download %s" % url))
            return -1, None

        if (response.status_code != 200):
            self.logger.warn("http response: %s %s" % (response.status_code, url))
        else:
            html = response.content.decode('utf-8', 'ignore')
            page = htmlparser.fromstring(html, base_url=url)
            if (css or javascript or image):
                if (css):
                    self.download_related_files(page, u"//link", u"href", outDir, assetDir, baseurl=url)
                if (javascript):
                    self.download_related_files(page, u"//script", u"src", outDir, assetDir, baseurl=url)
                if (image):
                    self.download_related_files(page, u"//img", u"src", outDir, assetDir, baseurl=url)

                newHtml = htmlparser.tostring(page)
                self.saveToFile(os.path.join(outDir, filename), newHtml)
            else:
                self.saveToFile(os.path.join(outDir, filename), html)
        return response.status_code, page



if __name__ == '__main__':
    downloader = urldownloader()
    downloader.download_page("https://watsi.org/fund-treatments/page/130",
                             "G:\\Tmp\\1\\2\\3\\html.files",
                             "G:\\Tmp\\1\\2\\3\\html.files\\assets",
                             "downloadTest.html",
                             css=True,
                             javascript=True,
                             image=False)