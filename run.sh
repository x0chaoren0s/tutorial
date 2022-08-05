# 小说
# sudo docker run -it --network=host -v /home/pi/tutorial:/tutorial -w /tutorial easypi/scrapyd scrapy crawl novel

# sshserver1
sudo docker run -d --network=host --name sshserver1 -v /home/pi/tutorial:/tutorial -w /tutorial easypi/scrapyd scrapy crawl sshservers1_v3

# sshserver2
sudo docker run -d --network=host --name sshserver2 -v /home/pi/tutorial:/tutorial -w /tutorial easypi/scrapyd scrapy crawl sshservers2

# sshserver3
sudo docker run -d --network=host --name sshserver3 -v /home/pi/tutorial:/tutorial -w /tutorial easypi/scrapyd scrapy crawl sshservers3

# sshserver4
sudo docker run -d --network=host --name sshserver4 -v /home/pi/tutorial:/tutorial -w /tutorial easypi/scrapyd scrapy crawl sshservers4


# glider
docker run -p 7605:7605 -p 7606:7606 --name glider -d -v C:\Users\60490\Desktop\tutorial\momomo2:/momomo2 nadoo/glider -config /momomo2/glider.conf 

# glider_gmsr
docker run -p 7608:7608 -p 7609:7609 --name glider_gmsr -d -v C:\Users\60490\Desktop\tutorial\momomo2:/momomo2 nadoo/glider -config /momomo2/glider_gmsr.conf

# glider_gmsr_3060
docker run -p 7610:7610 -p 7611:7611 --name glider_gmsr_3060 -d -v C:\Users\60490\Desktop\tutorial\momomo2:/momomo2 nadoo/glider -config /momomo2/glider_gmsr_3060.conf
