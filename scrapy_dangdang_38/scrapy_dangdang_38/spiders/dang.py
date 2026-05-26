import scrapy

from scrapy_dangdang_38.items import ScrapyDangdang38Item


class DangdangSpider(scrapy.Spider):
    name = "dang"
    allowed_domains = ["dangdang.com"]
    start_urls = ["https://category.dangdang.com/cp01.05.06.00.00.00.html"]
    page = 1

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.dangdang.com/",
            "Upgrade-Insecure-Requests": "1"
        }
        # 👇 只加这一行，让请求带上 headers
        yield scrapy.Request(self.start_urls[0], headers=headers, callback=self.parse)

    base_url = 'https://category.dangdang.com/pg3-cp01.05.06.00.00.00.html'
    def parse(self, response):

        li_list = response.xpath('//*[@id="component_59"]/li')

        for li in li_list:
            src = li.xpath('.//img/@data-original').get()
            if not src:
                src = li.xpath('.//img/@src').get()
            if src and src.startswith('//'):
                src = 'https:' + src

            name = li.xpath('.//img/@alt').get()

            price = li.xpath('.//p[@class="price"]/span[1]/text()').get()
            if not price:
                price = li.xpath('string(.//p[@class="price"])').get()

            print("图片：", src)
            print("书名：", name)
            print("价格：", price)
            print('-' * 50)

            book = ScrapyDangdang38Item(src=src,name=name,price=price)

            # 获取一个book就将book交给pipelines
            yield book

        # 每一页的爬取的业务逻辑全是一样的，所以我们只需要将执行的那个页的请求，再次调用parse方法即可
        # "https://category.dangdang.com/cp01.05.06.00.00.00.html" 1
        # "https://category.dangdang.com/pg2-cp01.05.06.00.00.00.html" 2
        # "https://category.dangdang.com/pg3-cp01.05.06.00.00.00.html" 3

        if self.page < 100:
            self.page = self.page + 1
            url = f"https://category.dangdang.com/pg{self.page}-cp01.05.06.00.00.00.html"
            # 怎么去调用自己
            # scrapy.Request就是scrapy的get请求
            # url 就是请求地址
            # callback是你要执行的那个函数， 注意不加()
            yield scrapy.Request(url=url,callback=self.parse)
