# packages required for framework integration
import framework
# module specific packages
import lxml.html as lh
import time
from datetime import datetime


class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', "source of hosts for module input (see 'info' for options)")
        self.register_option('limit', '100', 'no', "Maximum number of URLs to gather")
        self.info = {
            'Name': 'Starpage URL Retriever',
            'Author': '@vulp1n3',
            'Description': 'Retrieves URLs discovered by a wayback.archive.org search.',
            'Comments': ['Requirement: lxml.html Python module',
                         'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                         'Note: This search can return a LARGE number of results.',
                         'Note2: Some of the resulting URLs may no longer be valid.',
                         ]
        }

        self.source = 'WayBack search <http://wayback.archive.org>'
        self.url = 'http://wayback.archive.org/web/*/{0}*'
        self.table_name = 'urls'

        try:
            self.add_table(self.table_name, data=[['host','url','source','date']], header=True)
        except framework.FrameworkException:
            pass

    def add_url(self, host, url, source=None, date=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')):

        data = dict(
            host=self.to_unicode(host),
            url=self.to_unicode(url),
            source=self.to_unicode(source) or self.to_unicode(self.source),
            date=self.to_unicode(date),
        )
        return self.insert(self.table_name, data, ('host', 'url', 'source', 'date'))

    def module_run(self):

        hosts = self.get_source(self.options['source']['value'],
                'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')

        count = 0
        poss_urls = 0
        max_urls = int(self.options['limit']['value'])

        for host in hosts:
            req_url = self.url.format(host)
            self.verbose('URL is: %s' % req_url)

            self.output('Finding URLs for %s' % host)

            resp = self.request(req_url)
            date = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

            host_url_count = 0

            if resp.text:
                html = lh.fromstring(resp.text)
                root = html.getroottree()

                items = root.xpath(r'//a[parent::td[@class="url"]]/text()')
                if items:
                    self.output('Found %d URLs for %s (storing %d)' % (len(items), host, max_urls))
                    poss_urls += len(items)
                    for item in items:
                        count += 1
                        host_url_count += 1
                        #self.output('%d - %s' % (count, item))
                        self.output(item)
                        self.add_url(host, item, date=date)
                        if host_url_count >= max_urls:
                            break

            time.sleep(2)

        self.output('Stored %d of %d URLs found for %d hosts' % (count, poss_urls, len(hosts)))
