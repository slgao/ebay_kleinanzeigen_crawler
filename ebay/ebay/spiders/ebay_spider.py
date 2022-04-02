#! /usr/bin/env python
# coding=utf-8
# ================================================================
#   Copyright (C) 2022 * Ltd. All rights reserved.
#
#   Editor      : EMACS
#   File name   : ebay_spider.py
#   Author      : slgao
#   Created date: Sa Apr 02 2022 11:39:46
#   Description :
#
# ================================================================
import scrapy
import itertools as it
import pandas as pd
from pathlib import Path


class EbaySpider(scrapy.Spider):
    name = "ebay"
    url = 'https://www.ebay-kleinanzeigen.de'
    search_string = 'Kaffeemühle'
    city_parameter = 'k0l3331'
    page = range(1, 2, 1)
    url_sub_string = f'/{search_string}/{city_parameter}'
    start_urls = [
        'https://www.ebay-kleinanzeigen.de/s-berlin/' + url_sub_string
    ]
    item_dict = {}
    items = []

    def strip_string(self, string):
        if string and isinstance(string, str):
            string = string.strip()
        elif not string:
            return None
        return string

    def parse(self, response):
        items = response.css('li.ad-listitem')
        for item in items:
            item_title = item.css('a.ellipsis::text').get()
            item_description = item.css(
                'p.aditem-main--middle--description::text').get()
            item_price = item.css('p.aditem-main--middle--price::text').get()
            try:
                geo_location = item.css(
                    'div.aditem-main--top--left::text').getall()[-1]
            except IndexError:
                geo_location = item.css(
                    'div.aditem-main--top--left::text').getall()
            item_title = self.strip_string(item_title)
            item_description = self.strip_string(item_description)
            item_price = self.strip_string(item_price)
            geo_location = self.strip_string(geo_location)
            href = item.css('a::attr(href)').get()
            if href:
                item_url = self.url + href
            # print(item_title, item_description, item_price, geo_location,
            # item_url)
            self.items.append([
                item_title, item_description, item_price, geo_location,
                item_url
            ])
        current_page = response.css('span.pagination-current::text').get()
        print(current_page)
        pages = response.css('a.pagination-page')
        pages_url_list = pages.css('a::attr(href)').getall()
        next_page_string = 'seite:' + str(int(current_page) + 1)
        next_page_index = [
            i for i, p in enumerate(pages_url_list) if next_page_string in p
        ]
        if next_page_index:
            next_page_index = next_page_index[0]
        else:
            return
        next_page_url = self.url + pages_url_list[next_page_index]
        self.item_df = pd.DataFrame(
            self.items,
            columns=['title', 'description', 'price', 'location', 'url'])
        self.item_df.dropna(inplace=True)
        if int(current_page) == 1:
            writer = pd.ExcelWriter('items.xlsx', mode='w')
        else:
            writer = pd.ExcelWriter('items.xlsx',
                                    mode='a',
                                    if_sheet_exists='replace')
        self.item_df.to_excel(writer, 'sheet1', index=False)
        writer.save()
        yield scrapy.Request(next_page_url, callback=self.parse)
