from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
from parsetoword import AmebloEntry, AmebloImage, AmebloText, convert_to_word
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

def get_converter(options):
    if options.blog is not None:
        if options.entry is not None:
            return AmebloEntryToWordConverter(options)
        elif options.page is not None:
            return AmebloPageToWordConverter(options)
        elif options.first_page is not None and options.last_page is not None:
            return AmebloMultiplePagesToWordConverter(options)
        else:
            return AmebloToWordConverter(options)
    else:
        return AmebloToWordConverter(options)

class AmebloToWordConverter(object):
    LINK_SYNTAX = "" 
    def __init__(self, options):
        self._assertOptions(options)
        self.blog = options.blog
        self.output = options.output
    
    def _assertOptions(self, options):
        if not hasattr(options, 'blog'):
            raise AttributeNotFound('blog')
        if not hasattr(options, 'output'):
            raise AttributeNotFound('output')

    def _create_link(self):
        return self.LINK_SYNTAX

    def perform_conversion(self):
        soup = None
        for article in self._get_blog_articles(self._create_link()):
            ameblo_item = self._build_ameblo_data(article)
            convert_to_word(ameblo_item, self.output)

    def _get_blog_articles(self, link):
        req = requests.get(link)
        soup = BeautifulSoup(req.text, "lxml")
        for article in soup.find_all('article', attrs={'amb-component' : self._get_amb_component(), 'data-unique-ameba-id' : self.blog}):
            yield article

    def _get_amb_component(self):
        pass

    def _get_header_element(self):
        pass

    def _build_ameblo_data(self, article):
        ameblo_item = AmebloEntry()
        for title in article.find(self._get_header_element(), {'amb-component' : 'entryTitle'}):
            if isinstance(title, Tag):
                ameblo_item.link = title.get('href')
                ameblo_item.title = title.contents[0]
        for entry_date in article.find('p', {'amb-component' : 'entryDate'}):
            if isinstance(entry_date, Tag):
                content = None
                if len(entry_date.contents) > 1:
                    content = entry_date.contents[1]
                else:
                    content = entry_date.contents[0]
                ameblo_item.date = datetime.strptime(content, '%Y-%m-%d %H:%M:%S')

        contents = []
        for entry_content in article.find('div', {'amb-component' : 'entryBody'}):
            if isinstance(entry_content, Tag):
                img = entry_content.find('img')
                if img is not None:
                    contents.append(AmebloImage(img.get('src')))
                elif len(entry_content.contents) > 0 and isinstance(entry_content.contents[0], Tag):
                    for child in entry_content.contents[0].children:
                        contents.append(AmebloText(child))
                else:
                    contents.append(AmebloText(entry_content.contents[0]))
            elif isinstance(entry_content, NavigableString):
                contents.append(AmebloText(entry_content))
        ameblo_item.contents = contents
        return ameblo_item

class AmebloEntryToWordConverter(AmebloToWordConverter):
    LINK_SYNTAX = "http://ameblo.jp/%s/entry-%s.html"
    def __init__(self, options):
        super(AmebloEntryToWordConverter, self).__init__(options)
        self.blog = options.blog
        self.entry = options.entry

    def _assertOptions(self, options):
        super(AmebloEntryToWordConverter, self)._assertOptions(options)
        if not hasattr(options, 'entry'):
            raise AttributeNotFound('entry')

    def _get_amb_component(self):
        return 'entry'

    def _get_header_element(self):
        return 'h1'

    def _create_link(self):
        return self.LINK_SYNTAX % (self.blog, self.entry)

class AmebloPageToWordConverter(AmebloToWordConverter):
    LINK_SYNTAX = "http://ameblo.jp/%s/page-%s.html"
    def __init__(self, options):
        super(AmebloPageToWordConverter, self).__init__(options)
        self.blog = options.blog
        self.page = options.page

    def _assertOptions(self, options):
        super(AmebloPageToWordConverter, self)._assertOptions(options)
        if not hasattr(options, 'page'):
            raise AttributeNotFound('page')
        if not options.page.isdigit() or int(options.page) < 0:
			raise ValueError("Page number must be a positive digit")

    def _get_int(self, int_str):
		return int(int_str)

    def _get_amb_component(self):
        return 'entryStdTop'

    def _get_header_element(self):
        return 'h2'

    def _create_link(self):
        return self.LINK_SYNTAX % (self.blog, self.page)

class AmebloMultiplePagesToWordConverter(AmebloToWordConverter):
    LINK_SYNTAX = "http://ameblo.jp/%s/page-%s.html"
    def __init__(self, options):
        super(AmebloMultiplePagesToWordConverter, self).__init__(options)
        self.blog = options.blog
        self.first_page = options.first_page
        self.last_page = options.last_page

    def _assertOptions(self, options):
        super(AmebloMultiplePagesToWordConverter, self)._assertOptions(options)
        if not hasattr(options, 'first_page'):
            raise AttributeNotFound('first_page')
        if not hasattr(options, 'last_page'):
            raise AttributeNotFound('last_page')
        if not options.first_page.isdigit() or int(options.first_page) < 0:
            raise ValueError("Page number must be a positive digit")
        if not options.last_page.isdigit() or int(options.last_page) < 0:
            raise ValueError("Page number must be a positive digit")
        if int(options.first_page) >= int(options.last_page):
            raise ValueError("First page number is greater than last page")

    def _get_amb_component(self):
        return 'entryStdTop'

    def _get_header_element(self):
        return 'h2'

    def perform_conversion(self):
        soup = None
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_link = {}
            for link in self._create_link():
                future_to_link.update({executor.submit(self.convert, link): link})

            for future in as_completed(future_to_link):
                url = future_to_link[future]
                if future.exception() is not None:
                    print('%s generated an exception: %s' % (url,
                                                            future.exception()))
                else:
                    print('%s page' % (url))

    def convert(self, link):
        for article in self._get_blog_articles(link):
            ameblo_item = self._build_ameblo_data(article)
            convert_to_word(ameblo_item, self.output)

    def _create_link(self):
        links = []
        first_int = int(self.first_page)
        last_int = int(self.last_page)
        for page_number in range(first_int, last_int + 1):
            links.append(self.LINK_SYNTAX % (self.blog, page_number))
        return links

class AttributeNotFound(Exception):
    pass