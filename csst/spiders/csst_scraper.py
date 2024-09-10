import scrapy
from datetime import datetime
from logging import warning
from csst.items import MySpiderItem

#
# https://www.youtube.com/@NVA_code_fun_n_stuff
#

class CsstSpider(scrapy.Spider):
    name = 'csst_spider'
    start_urls = ['http://journal26.magtechjournal.com/kjkxjs/CN/article/showOldVolumnSimple.do']

    def parse(self, response):
        for a in response.css('a'):
            next_url = f'http://journal26.magtechjournal.com/kjkxjs/CN{a.attrib["href"].replace("..", "")}'
            i_n = a.css("::text").get().split(".")[1].replace("0", "")

            issue_number = {"issue_number":i_n}
            yield scrapy.Request(next_url, callback=self.parse_issue_page, cb_kwargs=issue_number)

    def parse_issue_page(self, response, issue_number):
        for article_url in response.css('a.txt_biaoti::attr(href)').getall()[1:2]:
            issue_number = {"issue_number":issue_number}
            yield scrapy.Request(article_url, callback=self.parse_article, cb_kwargs=issue_number)

    def parse_article(self, response, issue_number):

        try:

            item = MySpiderItem()

            item['html_to_ingest'] = response.body.decode('utf-8')
            item['pdf_to_download'] = f"""http://journal26.magtechjournal.com/kjkxjs/CN/article/downloadArticleFile.do?attachType=PDF&id={response.css("a.black-bg.btn-menu::attr(onclick)").get().split("'")[3]}"""
            item['original_link'] = response.url
            item['issue_number'] = issue_number
            
            date = ""
            for span in response.css('ul.list-unstyled.code-style li span').getall():
                if "出版日期:" in span:
                    try:
                        date = span.split("</code>")[1].replace("</span>", "").strip()
                    except Exception:
                        continue

            item['year_number'] = date.split("-")[0]
            item['publish_date'] = datetime.strptime(date, "%Y-%m-%d")

            item['title'] = response.css('h3.abs-tit::text').get().strip()
            a_n_tag = response.css('div.col-md-12 p span::text').getall()[3]
            item['article_number'] = a_n_tag.split(":")[-1].replace(".", "").strip() if a_n_tag else "0"     
            item['authors'] = response.css('p[data-toggle="collapse"] span::text').getall()[0].strip()
            item['abstract'] = response.css('div.panel-body.line-height.text-justify p::text').getall()[0]
            
            yield item
        except Exception as e:
            warning(f"There's been a goddamn problem: {e}")