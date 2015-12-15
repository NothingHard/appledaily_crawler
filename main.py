#coding: utf-8
import datetime
import time
import os
import sys
import getopt
import logging
import urlparse
import re

import urllib3
import traceback
#from lxml import etree
from lxml import html as htmlparser
#from urlparse import urlparse
import ast
import urldownloader

import sys
reload(sys)
sys.setdefaultencoding("utf8")

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Log:
    @staticmethod
    def d(text):
        logger.debug(text)

    @staticmethod
    def e(text):
        logger.error(text)

    @staticmethod
    def i(text):
        logger.info(text)

    @staticmethod
    def w(text):
        logger.warn(text)

    @staticmethod
    def print_exception(ex, msg=None):
        trace = traceback.format_exc()
        logger.exception(trace)
        logger.exception("*"+str(ex))
        logger.exception("*"+msg)




class Crawler(object):
    cache_key_id = "id"
    cache_key_progress = "progress"
    cache_key_raised = "raised"
    cache_key_togo = "togo"
    cache_key_donors = "donors"

    def __init__(self):
        self.interval = 300
        self.downloader = urldownloader.urldownloader()
        self.screenshotsDir = None
        self.htmlDir = None
        self.profileDir = None
        self.outputDir = os.getcwd()
        self.debugMode = False
        self.isLogToFile = False
        self.logFileHandler = None
        self.assetDir = None
        self.dictAssetFiles = {}

        #sys.setdefaultencoding("utf-8")
        self.processArgs()
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)
        self.initLogger(os.path.join(self.outputDir, 'log.txt') if self.isLogToFile else None)
        self.screenshotsDir = os.path.join(self.outputDir, "screenshots" + os.sep)
        self.htmlDir = os.path.join(self.outputDir, "html.files" + os.sep)
        self.assetDir = os.path.join(self.htmlDir, "assets" + os.sep)
        self.profileDir = os.path.join(self.outputDir, "profiles" + os.sep)
        if not os.path.exists(self.screenshotsDir):
            os.makedirs(self.screenshotsDir)
        if not os.path.exists(self.htmlDir):
            os.makedirs(self.htmlDir)
        if not os.path.exists(self.profileDir):
            os.makedirs(self.profileDir)
        if not os.path.exists(self.assetDir):
            os.makedirs(self.assetDir)

        self.dictPatientInfos = {}
        self.patientInfosFile = None
        self.patientInfosFilename = os.path.join(self.outputDir, 'patients.cache');
        self.loadPatientInfos()

        self.printArgs()

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
                Log.i("%d patient infos loaded" % len(self.dictPatientInfos))
            except Exception, ex:
                Log.print_exception(ex, "Can't read cache file")
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
            Log.print_exception(ex, "error: can't write cache file")
        finally:
            if (file):
                file.close()
        if (len(self.dictPatientInfos) > 0):
            for key in self.dictPatientInfos:
                self.cache_profile_detailsWithDict(self.dictPatientInfos[key])
            Log.i("%d patient infos saved" % len(self.dictPatientInfos))

    def freeResource(self):
        if (self.logFileHandler):
            self.logFileHandler.close()
        if (self.patientInfosFile):
            self.patientInfosFile.close()

    def initLogger(self, filename):
        logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(levelname)s %(filename)s[line:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

        if (filename):
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s[line:%(lineno)d] %(message)s')
            self.logFileHandler = logging.FileHandler(filename, mode='w', encoding="utf-8")
            self.logFileHandler.setLevel(logging.WARN)
            self.logFileHandler.setFormatter(formatter)
            logger.addHandler(self.logFileHandler)

        # for handler in logging.root.handlers:
        #     handler.addFilter(logging.Filter('foo'))

    # def initLogger(self, filename):
    #     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #     # Setup console handler
    #     consoleHandler = logging.StreamHandler()
    #     consoleHandler.setLevel(logging.NOTSET)
    #     consoleHandler.setFormatter(formatter)
    #
    #     # Setup file handler
    #     if (filename):
    #         self.logFileHandler = logging.FileHandler(filename, mode='w', encoding="utf-8")
    #         self.logFileHandler.setLevel(logging.DEBUG)
    #         self.logFileHandler.setFormatter(formatter)
    #
    #     # Setup Logger
    #     logger.addHandler(consoleHandler)
    #     if (filename):
    #         logger.addHandler(self.logFileHandler)
    #     logger.setLevel(logging.INFO)

    def read_last_line(filename):
        if not os.path.isfile(filename):
            return None
        with open(filename, 'rb') as fh:
            first = next(fh)
            offs = -100
            while True:
                fh.seek(offs, 2)
                lines = fh.readlines()
                if len(lines) > 1:
                    last = lines[-1]
                    return last
                offs *= 2

            #only one line
            fh.seek(0, 2)
            lines = fh.readlines()
            return lines[-1]

    def get_attrib(self, node, name, default=None):
        if (node == None):
            return default
        return node.attrib[name] if name in node.attrib else default

    def set_attrib(self, node, name, value):
        if (node == None):
            return
        node.attrib[name] = value

    def find_element_by_xpath(self, element, xpath):
        try:
            nodes = element.xpath(xpath)
            return nodes[0] if len(nodes) > 0 else None
        except:
            return None

    def find_elements_by_xpath(self, element, xpath):
        try:
            nodes = element.xpath(xpath)
            return nodes
        except:
            return None

    # def find_element_by_link_text(self, element, text):
    #     try:
    #         node = element.find_element_by_link_text(text)
    #         return node
    #     except:
    #         return None

    def save_profile_details(self, filename, list):
        file = None
        try:
            file = open(filename, mode='a')
            #file.write(u'\ufeff')  #codecs.BOM_UTF8
            file.write('\t'.join(list))
            file.write(os.linesep)
            file.flush()
        except Exception as ex:
            Log.print_exception(ex, "unable to save file: %s\n\t%s" % (filename))
        finally:
            if (file):
                file.close()

    def printUsage(self):
        print('%s -h -o <outputDir> --debug --interval=300 --logfile' % (os.path.basename(sys.argv[0])))

    def printArgs(self):
        Log.i("debug=%s" % (self.debugMode))
        Log.i("logfile=%s" % (self.isLogToFile))
        Log.i("outputDir=%s" % (self.outputDir))
        Log.i("screenshotsDir=%s" % (self.screenshotsDir))
        Log.i("htmlDir=%s" % (self.htmlDir))
        Log.i("profileDir=%s" % (self.profileDir))
        Log.i("interval=%s" % (str(self.interval) if self.interval else "n/a"))
        Log.i("")

    def processArgs(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:", ["debug", "logfile", "interval="])
            for opt, arg in opts:
                if opt == '-h':
                    self.printUsage()
                    sys.exit()
                elif opt in ("--debug"):
                    self.debugMode = True
                elif opt in ("--logfile"):
                    self.isLogToFile = True
                elif opt in ("--interval"):
                    self.interval = int(arg)
                #elif opt in ("-o", "--ofile"):
                elif opt in ("-o"):
                    self.outputDir = arg
        except getopt.GetoptError:
            self.printUsage()
            sys.exit(2)

    def run(self):
        http_pool = urllib3.HTTPSConnectionPool('watsi.org')  #HTTPS
        self.parsePages(http_pool)

    def parsePages(self, http_pool):
        try:
            pageIndex = 1
            #urlNextPage = 'https://watsi.org/fund-treatments/page/129'
            urlNextPage = 'https://watsi.org/fund-treatments/'
            while True:
                Log.i('downloading page %d...' % pageIndex)
                currentPage = urlNextPage
                status, page = self.downloader.download_page(currentPage,
                                                             self.htmlDir,
                                                             self.assetDir,
                                                             'page%05d.html' % (pageIndex),
                                                             css=False,
                                                             javascript=False,
                                                             image=False)

                if (status != 200):
                    Log.w("http response: %s %s" % (status, currentPage))
                    break
                else:
                    Log.i('parsing page %d...' % pageIndex)
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
                            list = re.findall(r"[\w,']+", progressStr)
                            progress = None
                            for i in range(0, len(list) - 1, 1):
                                item = list[i]
                                if (item != None and item.lower() == 'width'):
                                    progress = list[i + 1]

                            #togo raised donors
                            togo = None
                            raised = None
                            donors = None
                            list = re.findall(r"[\w,']+", title)
                            if (len(list) == 4):
                                if (list[1] != None and list[1].lower() == "raised"):
                                    raised = list[0]
                                    donors = list[2]
                                else:
                                    togo = list[0]
                                    donors = list[2]
                            else:
                                pass
                            #Log.i("%s %s" %(id, progress))
                            #Log.i("%s %s" %(id, urlProfile))
                            # Log.i("%s %s" %(id, title))
                            # Log.i("\t%s" % description)
                            # Log.i("\t%s" % imgSrc)
                            if (self.getPrevProgressById(id) != '100'):
                                self.parseProfile(http_pool, id, urlProfile)
                            self.cache_profile_details(id, progress, raised, togo, donors)
                        Log.i("%d items found" % (len(items)))
                    if (not items):
                        Log.i("items not found")
                        break
                    if (len(items) == 0):
                        Log.i("items length == 0")
                        break
                    if (not urlNextPage):
                        Log.i("NextPage not found")
                        break
                    pageIndex += 1
            self.savePatientInfos()
            Log.i('done!')
        except Exception as ex:
            Log.print_exception(ex, "parsePages")
        finally:
            pass

    def parseProfile(self, http_pool, name, urlProfile):
        try:
            Log.i('downloading profile %s...' % name)
            status, page = self.downloader.download_page(urlProfile,
                                                         self.profileDir,
                                                         self.assetDir,
                                                         '%s.html' % (name),
                                                         css=True,
                                                         javascript=True,
                                                         image=False)
            if (status != 200):
                Log.w("http response: %s %s" % (status, urlProfile))
            else:
                detailedFound = False
                progress = ""
                raised = ""
                togo = ""
                patients = ""
                nodeDetailes = self.find_element_by_xpath(page, u'//div[@id="funding_details"]')
                text = htmlparser.tostring(nodeDetailes, "innerHTML")
                if (text != None and text != ""):
                    list = re.findall(r"[\d,']+", text)
                    text = text.lower()
                    if (len(list) == 2):
                        if (text.find("raised")):
                            progress = list[0]
                            raised = list[1]
                            detailedFound = True
                        elif (text.find("to go")):
                            progress = list[0]
                            togo = list[1]
                            detailedFound = True
                    elif (len(list) == 1):
                        patients = list[0]
                        detailedFound = True




                #nodeDetailes = self.find_element_by_xpath(page, u'//div[@id="funding_details"]')
                # node = self.find_element_by_xpath(nodeDetailes, u'.//div[@class="left"]/span[1]')
                # progress = node.text if (node != None) else None
                # node = self.find_element_by_xpath(nodeDetailes, u'.//div[@class="right"]/span[1]')
                # togo = node.text if (node != None) else None
                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                if (not detailedFound):
                    Log.e("profile %s details not found" % name)
                else:
                    details = [timestamp, progress, raised, togo, patients]
                    Log.i("profile %s details: %s" % (name, str(details)))
                    self.save_profile_details(os.path.join(self.profileDir, '%s.txt' % (name)), details)
        except Exception as ex:
            Log.print_exception(ex, "Exception: %s: %s " % ("parseProfile", name))
        finally:
            pass


def _quit():
    print 'Exiting...'


if __name__ == '__main__':
    # root = Tk.Tk()
    # QuitButton = Tk.Button(master=root, text='Quit', command=_quit) #the quit button
    # QuitButton.pack(side=Tk.BOTTOM)


    crawler = Crawler()
    try:
        while True:
            crawler.run()
            print "press Ctrl+C to exit or wait for %d seconds to contine" % crawler.interval
            t = time.time()
            while True:
                time.sleep(1)
                if (time.time() - t > crawler.interval):
                    break
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    crawler.freeResource()
    print("bye!")