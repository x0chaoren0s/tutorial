# 小说
# sudo docker run -it --network=host -v /home/pi/tutorial:/tutorial -w /tutorial easypi/scrapyd scrapy crawl novel

# sshserver1
sudo docker run -it --network=host -v /home/pi/tutorial:/tutorial -w /tutorial easypi/scrapyd scrapy crawl sshservers1_v3

# sshserver2
# sudo docker run -it --network=host -v /home/pi/tutorial:/tutorial -w /tutorial easypi/scrapyd scrapy crawl sshservers2