# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

# 如果想使用管道的话 那么就必须在setting中来开启管道
class ScrapyDangdang38Pipeline:
    # 在爬虫开始的之前就执行的一个方法
    def open_spider(self, spider):
        self.fp = open('book.json','w',encoding='utf8')

    # item就是yield后面的book对象
    def process_item(self, item, spider):
        # 以下这种模式不推荐 因为每传递一个对象 就打开一次文件 对文件操作过于频繁 在前后加入open和close方法
        # write 方法必须要写一个字符串 而不能是其他的对象
        # w模式 会每一个对象都打开一次文件 覆盖之前的内容 需要改a模式
        # with open('book.json','a',encoding='utf8') as fp:
        #     fp.write(str(item))
        self.fp.write(str(item))
        return item

    # 在爬虫文件执行完成之后 执行的方法
    def close_spider(self,spider):
        self.fp.close()

import urllib.request
# 多条管道开启
# （1）定义管道类
# （2）在settings中开启管道
# "scrapy_dangdang_38.pipelines.DangDangDownloadPipeline": 301,
class DangDangDownloadPipeline:
    def process_item(self, item, spider):

        url = item.get('src')
        name = item.get('name').strip()
        name = re.sub(r'[\\/*?:"<>|]', '', name)
        filename = './books/' + name + '.jpg'

        urllib.request.urlretrieve(url=url,filename=filename)

        return item


# 加载setting文件
from scrapy.utils.project import get_project_settings
import pymongo

class MongoPipeline:
    def open_spider(self, spider):
        self.client = pymongo.MongoClient('localhost', 27017)
        self.db = self.client['dangdang']
        self.collection = self.db['books']

    def process_item(self, item, spider):
        self.collection.insert_one(dict(item))
        return item

    def close_spider(self, spider):
        self.client.close()

