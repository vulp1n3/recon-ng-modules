# packages required for framework integration
import framework
# module specific packages
import lxml.html as lh
import time


class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', "source of hosts for module input (see 'info' for options)")
        self.info = {
            'Name': 'Starpage URL Retriever',
            'Author': '@vulp1n3',
            'Description': 'Retrieves URLs discovered by Startpage domain search.',
            'Comments': ['Requirement: lxml.html Python module',
                         'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                         ]
        }

        self.url = 'https://startpage.com/do/search?'
        self.table_name = 'urls'

        try:
            self.add_table(self.table_name, data=[['host','url']], header=True)
        except framework.FrameworkException:
            pass

    def add_url(self, host, url):
        data = dict(
            host=self.to_unicode(host),
            url=self.to_unicode(url),
        )
        return self.insert(self.table_name, data, ('host', 'url'))

    def module_run(self):
        self.verbose('URL is: %s' % self.url)

        hosts = self.get_source(self.options['source']['value'],
                'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')

        count = 0
        for host in hosts:

            self.output('Finding URLs for %s' % host)

            data = {"cat":"web",
                "cmd":"process_search",
                "language":"english",
                "enginecount":"1",
                "pl":"",
                "tss":"1",
                "ff":"",
                "theme":"",
                "suggestOn":"0",
                "flag_ac":"0",
                "lui":"english",
                "query":"host:{0}".format(host),
                "prfh":"sslEEE1N1Nfont_sizeEEEmediumN1Nrecent_results_filterEEE1N1Nlanguage_uiEEEenglishN1Ndisable_open_in_new_windowEEE1N1Nnum_of_resultsEEE200N1NlanguageEEEenglishN1N&suggestOn=0"}


            resp = self.request(self.url, method='POST', payload=data)

            if resp.text:
                html = lh.fromstring(resp.text)
                root = html.getroottree()

                items = root.xpath(r'//@href[parent::a[parent::h3[parent::div[@class="result"]]]]')
                if items:
                    self.output('Found %d URLs for %s' % (len(items), host))
                    for item in items:
                        count += 1
                        self.output(item)
                        self.add_url(host, item)

            time.sleep(2)

        self.output('Found %d URLs for %d hosts' % (count, len(hosts)))
