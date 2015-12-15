import re



class StrHelper:
    @staticmethod
    def trim(text):
        if(text==None or text==""):
            return ""
        return text.strip()


    @staticmethod
    def strToValue(text):
        return re.sub(ur"[^0-9\.]", "", text)