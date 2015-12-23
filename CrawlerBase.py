# coding: utf-8
import os
import sys
import getopt
import logging
import datetime
import time
from EmailHelper import EmailHelper
from LogHelper import LogHelper
from LogCounterHandler import LogCounterHandler
import urldownloader
import csv
import operator

overallFileName = 'overall.csv'
overallSortedFileName = 'overall_sorted.csv'


class CrawlerBase(object):
    def __init__(self):
        self.logger = logging.getLogger(LogHelper.LoggerName)
        self.interval = None
        self.downloader = urldownloader.urldownloader()
        self.htmlDir = None
        self.profileDir = None
        self.outputDir = os.getcwd()
        self.debugMode = False
        self.logFileHandler = None
        self.assetDir = None
        self.dictAssetFiles = {}
        self.lastErrorReportTime = time.time()

        #sys.setdefaultencoding("utf-8")
        self.processArgs()
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)
        self.htmlDir = os.path.join(self.outputDir, "html.files" + os.sep)
        self.assetDir = os.path.join(self.htmlDir, "assets" + os.sep)
        self.profileDir = os.path.join(self.outputDir, "profiles" + os.sep)
        self.logDir = os.path.join(self.outputDir, "logs" + os.sep)
        if not os.path.exists(self.htmlDir):
            os.makedirs(self.htmlDir)
        if not os.path.exists(self.profileDir):
            os.makedirs(self.profileDir)
        if not os.path.exists(self.assetDir):
            os.makedirs(self.assetDir)
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)

        self.initLogger()
        self.printArgs()

        self.overallEntriesFile = None
        self.overallEntriesWriter = None
        self.overallEntries = {}
        self.loadOverallEntries()

        self.overallEntriesPendingFile = None
        self.overallEntriesPendingWriter = None
        self.overallEntriesPending = {}
        self.loadOverallEntriesPending()

    def freeResource(self):
        if (self.logFileHandler):
            self.logFileHandler.close()
        if (self.overallEntriesFile != None):
            self.overallEntriesFile.close()
        if (self.overallEntriesPendingFile != None):
            self.overallEntriesPendingFile.close()

    def initLogger(self):
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(filename)s[line:%(lineno)d] %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

        self.logCounterHandler = LogCounterHandler(logging.WARN)
        self.logger.addHandler(self.logCounterHandler)

        filename = os.path.join(self.logDir,
                                '%s.txt' % datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S'))
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s[line:%(lineno)d] %(message)s')
        self.logFileHandler = logging.FileHandler(filename, mode='a', encoding="utf-8", delay=True)
        self.logFileHandler.setLevel(logging.WARN)
        self.logFileHandler.setFormatter(formatter)
        self.logger.addHandler(self.logFileHandler)

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

    def printUsage(self):
        print('%s -h -o <outputDir> --debug --interval=300' % (os.path.basename(sys.argv[0])))

    def printArgs(self):
        self.logger.info("debug=%s" % (self.debugMode))
        self.logger.info("outputDir=%s" % (self.outputDir))
        self.logger.info("htmlDir=%s" % (self.htmlDir))
        self.logger.info("profileDir=%s" % (self.profileDir))
        self.logger.info("interval=%s" % (str(self.interval) if self.interval else "n/a"))
        self.logger.info("")

    def processArgs(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:", ["debug", "logfile", "interval="])
            for opt, arg in opts:
                if opt == '-h':
                    self.printUsage()
                    sys.exit()
                elif opt in ("--debug"):
                    self.debugMode = True
                elif opt in ("--interval"):
                    self.interval = int(arg)
                #elif opt in ("-o", "--ofile"):
                elif opt in ("-o"):
                    self.outputDir = arg
        except getopt.GetoptError:
            self.printUsage()
            sys.exit(2)

    def run(self):
        try:
            while True:
                self.parsePages()
                self.sort_csv(os.path.join(self.profileDir, overallFileName),
                              os.path.join(self.profileDir, overallSortedFileName), (0,))
                self.sort_csv(os.path.join(self.profileDir, u"未結案" + os.sep + overallFileName),
                              os.path.join(self.profileDir, u"未結案" + os.sep + overallSortedFileName), (0,))

                if (self.logCounterHandler.logCount > 0 and time.time() - self.lastErrorReportTime > 2 * 60 * 60):
                    dir, scriptName = os.path.split(sys.argv[0])
                    try:
                        EmailHelper.send("%s error report" % (scriptName), self.logCounterHandler.report())
                        self.lastErrorReportTime = time.time()
                        self.logCounterHandler.logCount = 0
                    except Exception as ex:
                        self.logger.exception(ex, "cannot sending email")
                if (self.interval == None):
                    break
                print "press Ctrl+C to exit or wait for %d seconds to continue" % self.interval
                t = time.time()
                while True:
                    time.sleep(1)
                    if (time.time() - t > self.interval):
                        break
        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt")
        except SystemExit:
            self.logger.info("SystemExit")
        except Exception as ex:
            self.logger.exception(ex, "Unknown error")
        self.freeResource()
        self.logger.info("bye!")

    def parsePages(self):
        pass

    def loadOverallEntries(self):
        filename = os.path.join(self.profileDir, overallFileName)
        if (os.path.isfile(filename)):
            with open(filename, 'rb') as csvfile:
                for row in csv.reader(csvfile):
                    if (len(row) > 0):
                        self.overallEntries[row[0]] = True

    def saveOverallEntry(self, id, values):
        if (id in self.overallEntries):
            return
        self.overallEntries[id] = True
        #self.logger.warn("saveOverallEntry -- overallEntry.title: %s" % overallEntry.title)

        if (self.overallEntriesWriter == None or self.overallEntriesFile == None):
            self.overallEntriesFile = open(os.path.join(self.profileDir, overallFileName), "ab")
            self.overallEntriesWriter = csv.writer(self.overallEntriesFile)
        self.overallEntriesWriter.writerow(values)
        self.overallEntriesFile.flush()

    def loadOverallEntriesPending(self):
        filename = os.path.join(self.profileDir, u"未結案" + os.sep + overallFileName)
        if (os.path.isfile(filename)):
            with open(filename, 'rb') as csvfile:
                for row in csv.reader(csvfile):
                    if (len(row) > 0):
                        self.overallEntriesPending[row[0]] = True

    def saveOverallEntryPending(self, id, values):
        if (id in self.overallEntriesPending):
            return
        self.overallEntriesPending[id] = True
        #self.logger.warn("saveOverallEntryPending -- overallEntryPending.title: %s" % overallEntryPending.title)

        if (self.overallEntriesPendingWriter == None or self.overallEntriesPendingFile == None):
            self.overallEntriesPendingFile = open(os.path.join(self.profileDir, u"未結案" + os.sep + overallFileName), "ab")
            self.overallEntriesPendingWriter = csv.writer(self.overallEntriesPendingFile)
        self.overallEntriesPendingWriter.writerow(values)
        self.overallEntriesPendingFile.flush()

    def sort_csv(self, csvFilename, dstFilename, sort_key_columns):
        data = []
        with open(csvFilename, 'rb') as f:
            for row in csv.reader(f):
                data.append(row)
                #data.append(convert(types, row))
        data.sort(key=operator.itemgetter(*sort_key_columns))
        with open(dstFilename, 'wb') as f:
            csv.writer(f).writerows(data)