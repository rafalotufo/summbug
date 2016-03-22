from BeautifulSoup import BeautifulSoup
import itertools, re, datetime, urllib2
import bugs, bug_retriever

default_debian_folder = '/Users/rlotufo/projects/bug-reports/debian/'

def to_text(soup):
    return ''.join([e for e in soup.recursiveChildGenerator() 
             if isinstance(e,basestring)]).strip().encode('ascii', 'ignore')

class DebianBugRetriever(object):
    def __init__(self, folder=default_debian_folder):
        '''rep is instance of BugRepository'''
        self.parser = DebianBugParser()
        self.rep = bug_retriever.BugRepository(folder) if folder else None

    def retrieve_bug(self, id, from_rep=True):
        if self.rep and from_rep and id in self.rep:
            bugstr = self.rep.read(id)
        else:
            bugstr = urllib2.urlopen(
                'http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=%d' % id).read()
            if self.rep:
                self.rep.save(id, bugstr)

        return self.parser.parse_bug(bugstr, id)

class DebianBugParser(object):
    def __init__(self):
        pass

    def parse_bug(self, bug_str, id):
        bug = BeautifulSoup(bug_str, convertEntities=BeautifulSoup.XML_ENTITIES)
        title = re.split('#\d+', to_text(bug.find('h1')))[1]

        def parse_comments(comments):
            def parse_header(header):
                def parse_date(date_str):
                    ## format can be either:
                    ## Tue, 16 May 2006 20:01:22 +0200
                    ## Sat, 3 Mar 2007 14:53:30 -0800 (PST)
                    ## 07 Jul 2006 08:17:40 -0700
                    ## 07 Jul 2006 08:17:40 GMT
                    remove_tz = lambda date_str: re.split('[\+-]\d{4}|[A-Z]{3]', date_str)[0]
                    remove_weekday = lambda date_str: re.split(',', date_str)[-1]
                    date_str = remove_weekday(remove_tz(date_str)).strip()
                    return datetime.datetime.strptime(date_str, '%d %b %Y %H:%M:%S')

                header = to_text(header)
                author = re.split('From:', re.split('To:', header)[0])[1].strip()
                try:
                    date = parse_date(re.split('Date:', header)[1].strip())
                except:
                    print id,header
                    date = datetime.datetime(1970, 01, 01, 0,0,0) ## some comments don't have a date
                return author, date

            def parse_message(message): 
                return to_text(message)

            for i, (header, message) in enumerate(comments):
                author, date = parse_header(header)
                text = parse_message(message)
                yield bugs.Comment(i, author, date, text)
        
        comments = list(parse_comments(itertools.izip(bug.findAll('pre', 'headers'),
                                                      bug.findAll('pre', 'message'))))

        desc = comments[0].text
        reporter = comments[0].author
        date = comments[0].date
        return bugs.BugReport('Debian', id, title, desc, reporter, date, comments)


