from bs4 import BeautifulSoup
from optparse import OptionParser

import requests
from scrap import get_converter

opt_parse = OptionParser()
opt_parse.add_option("-o", "--output", dest="output",
    help="Output folder")
opt_parse.add_option("-b", "--blog", dest="blog",
    help="Blog")
opt_parse.add_option("-e", "--entry", dest="entry",
    help="Blog entry")
opt_parse.add_option("-p", "--page", dest="page",
    help="Page")
opt_parse.add_option("-f", "--first_page", dest="first_page",
    help="First Page")
opt_parse.add_option("-l", "--last_page", dest="last_page",
    help="Last Page")

(options, args) = opt_parse.parse_args()
get_converter(options).perform_conversion()

# req = requests.get("http://ameblo.jp/wakeupgirls/entry-12277935275.html")
# soup = BeautifulSoup(req.text, "lxml")


# blog = 'wakeupgirls'

# for article in soup.find_all('article', attrs={'amb-component' : 'entry', 'data-unique-ameba-id' : blog}):
#     print type(article)