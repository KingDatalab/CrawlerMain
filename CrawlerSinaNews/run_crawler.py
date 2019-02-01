import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

process = CrawlerProcess(get_project_settings())
# running the different spiders seperately
#spider_name = 'CrawlerSinaNews'
spider_name = 'sina_news'

process.crawl(spider_name)
process.start()
