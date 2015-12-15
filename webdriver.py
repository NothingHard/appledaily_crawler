#coding: utf-8
import codecs
import io
import os
import sys, getopt
import logging

from selenium import webdriver
#from selenium.webdriver.phantomjs import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


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


class Crawler(object):
    def __init__(self):
        self.screenshotsDir = None
        self.htmlDir = None
        self.outputDir = os.getcwd()
        self.debugMode = False
        self.logFileHandler = None

        #sys.setdefaultencoding("utf-8")
        self.processArgs()
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)
        self.initLogger(os.path.join(self.outputDir, 'log.txt'))
        self.screenshotsDir = os.path.join(self.outputDir, "Screenshots" + os.sep)
        self.htmlDir = os.path.join(self.outputDir, "HTML" + os.sep)
        if not os.path.exists(self.screenshotsDir):
            os.makedirs(self.screenshotsDir)
        if not os.path.exists(self.htmlDir):
            os.makedirs(self.htmlDir)
        self.printArgs()

    def freeResource(self):
        if (self.logFileHandler):
            self.logFileHandler.close()

    def initLogger(self, filename):
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Setup console handler
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(logging.NOTSET)
        consoleHandler.setFormatter(formatter)

        # Setup file handler
        if (filename):
            self.logFileHandler = logging.FileHandler(filename, mode='w', encoding="utf-8")
            self.logFileHandler.setLevel(logging.DEBUG)
            self.logFileHandler.setFormatter(formatter)

        # Setup Logger
        logger.addHandler(consoleHandler)
        if (filename):
            logger.addHandler(self.logFileHandler)
        logger.setLevel(logging.INFO)

    def createWebdriver(self, javascriptEnabled=True, loadImage=True):
        Log.i('createWebdriver...')
        args = [
            #        '--output-encoding=utf8',
        ]
        if not (loadImage):
            args += ['--load-images=no']

        #The API specifies that desired capabilities be passed into the constructor. However, it may be the case that a driver does not support a feature requested in the desired capabilities. In that case, no error is thrown by the driver, and this is intentional. A capabilities object is returned by the session which indicates the capabilities that the session actually supports.
        capabilities = dict(DesiredCapabilities.CHROME)
        capabilities["javascriptEnabled"] = javascriptEnabled
        #capabilities["phantomjs.page.settings.userAgent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0 "
        #driver = webdriver.PhantomJS(service_args=args) # or add to your PATH
        driver = webdriver.PhantomJS(service_args=args,
                                     executable_path='E:\PortableAPP\PhantomJS\phantomjs.exe',
                                     desired_capabilities=capabilities)  #在IDE裏沒用指定path會找不到 phantomjs.exe
        driver.set_window_size(1024, 768)  # optional
        return driver

    def printCap(self, driver):
        cap_dict = driver.capabilities
        for key in cap_dict:
            print('%s: %s' % (key, cap_dict[key]))
        print(driver.current_url)

    def find_element_by_xpath(self, element, xpath):
        try:
            node = element.find_element_by_xpath(xpath)
            return node
        except:
            return None

    def find_elements_by_xpath(self, element, xpath):
        try:
            nodes = element.find_elements_by_xpath(xpath)
            return nodes
        except:
            return None

    def find_element_by_link_text(self, element, text):
        try:
            node = element.find_element_by_link_text(text)
            return node
        except:
            return None

    def saveTextToFile(self, filename, text):
        file = None
        try:
            file = codecs.open(filename, mode='w', encoding="utf-8")
            file.write(u'\ufeff')  #codecs.BOM_UTF8
            file.write(text)
        except Exception as ex:
            Log.e("unable to save file: %s\n\t%s" % (filename, str(ex)))
        finally:
            if (file):
                file.close()

    def printUsage(self):
        print('%s -h -o <outputDir> --debug' % (os.path.basename(sys.argv[0])))

    def printArgs(self):
        Log.i("debug=%s" % (self.debugMode))
        Log.i("outputDir=%s" % (self.outputDir))
        Log.i("screenshotsDir=%s" % (self.screenshotsDir))
        Log.i("htmlDir=%s" % (self.htmlDir))

    def processArgs(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:", ["debug"])
            for opt, arg in opts:
                if opt == '-h':
                    self.printUsage()
                    sys.exit()
                elif opt in ("--debug"):
                    self.debugMode = True
                #elif opt in ("-o", "--ofile"):
                elif opt in ("-o"):
                    self.outputDir = arg
        except getopt.GetoptError:
            self.printUsage()
            sys.exit(2)

    def run(self):
        webDriver=None
        try:
            webDriver = self.createWebdriver(javascriptEnabled=False, loadImage=False)

            #webDriver.get('http://www.mobile01.com/')
            #printCap(webDriver)

            #//a[text()='Next ›']/@href
            pageIndex = 1
            urlNextPage = 'https://watsi.org/fund-treatments/page/129'
            #urlNextPage = 'https://watsi.org/fund-treatments'
            while True:
                Log.i('downloading page %d...' % pageIndex)
                webDriver.get(urlNextPage)
                if (self.debugMode):
                    Log.i('saving page %d...' % pageIndex)
                    webDriver.save_screenshot(
                        os.path.join(self.screenshotsDir, 'page%05d.png' % (pageIndex)))  # save a screenshot to disk
                    self.saveTextToFile(os.path.join(self.htmlDir, 'page%05d.html' % (pageIndex)), webDriver.page_source)

                Log.i('parsing page %d...' % pageIndex)
                node = self.find_element_by_link_text(webDriver, "Next ›")
                urlNextPage = node.get_attribute("href") if (node) else None
                items = self.find_elements_by_xpath(webDriver, "//div[@class='profiles']/ul/li")
                if (items):
                    for item in items:
                        id = item.get_attribute("id")
                        node = self.find_element_by_xpath(item, ".//*[@class='info-bar']")  #info-bar 會在 <p> or <div> 中
                        title = node.get_attribute("innerText") if (node) else ""
                        node = self.find_element_by_xpath(item, ".//p[@class='profile-description']")
                        description = node.get_attribute("innerText") if (node) else ""
                        node = self.find_element_by_xpath(item, ".//div[@class='cont']/a/img")
                        imgSrc = node.get_attribute("src") if (node) else ""
                        # csvData=[id, title, imgSrc, description]
                        # Log.i("%s %s" %(id, title))
                        # Log.i("\t%s" % description)
                        # Log.i("\t%s" % imgSrc)
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
            Log.i('done!')
        finally:
            if(webDriver):
                webDriver.close()
                webDriver.quit()

if __name__ == '__main__':
    crawler = Crawler()
    crawler.run()
    crawler.freeResource()