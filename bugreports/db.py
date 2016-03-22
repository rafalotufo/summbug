import sqlite3, sys

import datetime, csv, logging, re
from pkg_resources import resource_stream
import mltk.sql as sql

android_db = '/Users/rlotufo/projects/bug-reports/android-bugs.db'
chrome_db = '/Users/rlotufo/projects/bug-reports/chrome-bugs.db'

chrome_today = datetime.datetime(2010, 5, 10)
android_today = datetime.datetime(2011, 5, 17)

status_mapping = dict(csv.reader(resource_stream(__name__, 'data/status-transform.csv')))


def translate_status(status):
    return status_mapping.get(status.lower(), status)

def translate_close_date(dt,today):
    """transforms string dt to datetime format based on today
    today returns today, yesterday returns today - 1"""
    try:
        return datetime.datetime.strptime(dt, '%b %Y')
    except ValueError:
        try:
            d = datetime.datetime.strptime(dt + ' %d' % today.year, '%b %d %Y')
            if d > today:
                return d - datetime.timedelta(365)
            else:
                return d
        except ValueError as e:
            if dt == 'Today': return today
            elif dt == 'Yesterday': return today - datetime.timedelta(1)
            else: raise e

def fix_author(a):
    return a.split()[-1]

def as_utf8(s):
    try:
        return unicode(str(s), 'utf-8')
    except UnicodeEncodeError:
        return ''

class Comment(object):
    def __init__(self, num, author, date, text, bug):
        self.bug = bug
        self.num = num
        self.date = datetime.datetime.fromtimestamp(date/1000)
        self.author = fix_author(author)
        self.text = as_utf8(text)

class BugReport:
    def __init__(self, id, title, desc, date, author, followers, status, close_date, today, comments=None):
        self.id = id
        self.title = as_utf8(title)
        self.desc = as_utf8(desc)
        self.author = fix_author(author)
        self.followers = followers
        self.status = translate_status(status)
        self.close_date = translate_close_date(close_date, today) if close_date else None
        self.comments = [] if comments == None else comments
        self.date = datetime.datetime.fromtimestamp(date/1000)


class BugReportDB(object):
    def __init__(self, sqlite_file, today):
        self.conn = sqlite3.connect(sqlite_file)
        self.conn.text_factory = sqlite3.OptimizedUnicode
        self.today = today

    def find_all(self):
        return self.find_by_id()

    def find_by_id(self, id=None):
        stmt = ('select id, title, descr, date, author, followers, m.value as status, m2.value as close_date ' 
                'from issue i ' 
                'join meta m on i.id = m.issueId and m.name like \'Status%\' ' 
                'left outer join meta m2 on i.id = m2.issueId and m2.name like \'Closed%\' ')
        if id: bugs = self.conn.execute(stmt + 'where id = ?', [id])
        else: bugs = self.conn.execute(stmt)
            
        for row in bugs:
            bug = BugReport(*row, today=self.today)
            for num,author,date,comment in self.conn.execute(
                'select num, author, date, comment from updates where issueId = ?', [bug.id]):
                bug.comments.append(Comment(num,author,date,unicode(comment), bug=bug))
#            all(map(lambda c: c.bug, bug.comments)) # debug
#            print >> sys.stderr, len(bug.comments)
            yield bug

    def all_report_ids(self):
        return map(lambda row: row[0], self.conn.execute('select id from issue'))

    def find_merges(self):
        conn = self.conn
        merged_into = dict()

        stmt = sql.select(sql.select_stmt('issueId', 'value').from_('tag').where('name = \'Mergedinto\''),
                          sql.select_stmt('issueId', 'value').from_('meta').where('name like \'Merged%\''))

        def clean(s):
            if isinstance(s, basestring):
                id = re.findall('-?\d+', s)
                if len(id) == 1:
                    return int(id[0])
                else:
                    return 0
            else: return s
        
        for dup,orig in stmt.execute(conn.cursor()):
            orig = clean(orig)
            dup = int(dup)
            if orig > 0:
                if str(merged_into.get(dup, orig)) != str(orig):
                    print >> sys.stderr, ('bad %s, %s, %s' % (dup, orig, merged_into[dup]))
                merged_into[dup] = orig
            else:
                if merged_into.get(dup,-1) == abs(orig):
                    del merged_into[dup]
        return merged_into

def serialize_bug(bug):
    def serialize_comment(c):
        r = dict(c.__dict__)
        del r['bug']
        return r

    r = dict(bug.__dict__)
    r['comments'] = map(serialize_comment, bug.comments)
    return r
