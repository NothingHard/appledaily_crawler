# chmod +x watsi.sh
# crotab: @reboot /usr/bin/screen -d -m -S Watsi ~/crawler/watsi.sh
/usr/bin/python /home/cslin/work/appledaily_crawler/crawler/Watsi.py -o /home/cslin/work/appledaily_crawler/crawler/watsi --interval=300
