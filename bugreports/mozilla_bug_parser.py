from BeautifulSoup import BeautifulSoup
import itertools, re, datetime, sys
import bugs
from util.monads import head

class AccessDenied(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class CantReadFile(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def to_text(soup):
    return ''.join([e for e in soup.recursiveChildGenerator() 
             if isinstance(e,basestring)]).strip().encode('ascii', 'ignore')

def parse_status(bug):
    ## return status, and, if duplicate, id of original bug
    status = bug.findAll(id='static_bug_status')
    if status:
        status = to_text(status[0])
        if re.search('DUPLICATE', status):
            dup_of = head(re.findall('bug (\d+)', status)).getOrElse(None)
        else: dup_of = None
        status, res = (status + ' NEW NEW').split()[:2]
        return (status, res, dup_of)
    else:
        return (None, None, None)
        print >> sys.stderr, 'not status for ...'

def parse_votes(bug):
    votes_re = re.compile('Votes \((\d+)\)')
    votes = head(bug.findAll(title=votes_re)).map(lambda v: votes_re.match(v['title']).group(1)).getOrElse(None)
    return votes

def parse_date(date_str):
    return datetime.datetime.strptime(date_str[:-4], '%Y-%m-%d %H:%M:%S')

def parse_comments(bug):
    comments = itertools.chain(bug.findAll('div', 'bz_first_comment'),
                               bug.findAll('div', 'bz_comment'))
    for i,c in enumerate(comments):
        head = c.find('div', 'bz_%scomment_head' % ('first_' if i == 0 else ''))
        ## class is 'bz_comment bz_first_comment' so it repeats; need to skip
        if i > 0 and re.search('first', c['class']): continue  
        elif head:
            time = to_text(head.find('span', 'bz_comment_time'))
            user = to_text(head.find('span', 'bz_comment_user'))
            text = to_text(c.find('pre', 'bz_comment_text'))
            yield bugs.Comment(i, user, parse_date(time), text)

def parse_bug(bug_html, id, project):
    try:
        bug = BeautifulSoup(bug_html, convertEntities=BeautifulSoup.XML_ENTITIES)

        title = to_text(bug.find('td', id='title'))
        if re.search('Access Denied', title):
            raise AccessDenied('Access denied to bug %d' % id)
    except ValueError:
        raise CantReadFile('Can\'t read bug %d' % id)

    comments = list(parse_comments(bug))
    reporter = comments[0].author
    open_date = comments[0].date
    desc = comments[0].text
    title = to_text(bug.find('td', id='subtitle'))
    votes = parse_votes(bug)
    status = parse_status(bug)
    return bugs.BugReport(project, id, title, desc, reporter, open_date, comments, followers=votes,
                          status=status[1], resolution=status[0], dupe_of=status[2])
