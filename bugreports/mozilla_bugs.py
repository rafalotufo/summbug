import zipfile, re, sys, json, logging, urllib2
from mozilla_bug_parser import parse_bug, AccessDenied, CantReadFile
import bug_retriever

default_mozilla_folder = '/Users/rlotufo/projects/bug-reports/mozilla/data/bugs'
index_fn = 'index.json'
basedir = '/Users/rlotufo/projects/bug-reports/mozilla/data/'
zipfiles = ['mozilla.bugs.1.zip',
             'mozilla.bugs.2.zip',
             'mozilla.bugs.3.zip',
             'mozilla.bugs.4.zip',
             'mozilla.bugs.5.zip']

def read_index(index_fn='%s/%s' % (basedir, index_fn)):
    return json.load(open(index_fn, 'r'))

def index_bugs(zipfiles=zipfiles, basedir=basedir, index_fn=index_fn):
    id_to_zipfile = dict()
    for zfile in zipfiles:
        z = zipfiles[zfile]
        for i,filename in enumerate(z.namelist()):
            if i % 10 == 0:
                sys.stderr.write('%d         \r' % i)
            bug_id = re.match('\d/(\d+)\.html', filename)
            if bug_id:
                bug_id = int(bug_id.group(1))
                id_to_zipfile[bug_id] = (zfile,filename)
    json.dump(id_to_zipfile, open('%s/%s' % (basedir, index_fn), 'w'))

def retrieve_bug_html(bug_id):
    return urllib2.urlopen(
        'https://bugzilla.mozilla.org/show_bug.cgi?id=%d' % bug_id).read()
    
    
class MozillaBugs(object):
    def __init__(self, index_fn=index_fn, basedir=basedir, zipfiles=zipfiles, bug_folder=default_mozilla_folder):
        self.index_fn = index_fn
        self.basedir = basedir
        self.zipfiles = zipfiles
        self._zips = {}
        self.id_to_zipfile = read_index()
        self.rep = bug_retriever.BugRepository(bug_folder) if bug_folder else None

    def zipfile(self, zip_file):
        '''lazy loading of zip files'''
        return self._zips.setdefault(zip_file, zipfile.ZipFile(basedir +'/' + zip_file, "r"))
        
    def retrieve_bug(self, id, from_rep=True):
        bugstr = None
        try:
            if from_rep:
                if self.rep and str(id) in self.rep:
                    bugstr = self.rep.read(id)
                else:
                    zfile, filename = self.id_to_zipfile[str(id)]
                    z = self.zipfile(zfile)
                    bugstr = z.read(filename)
        except KeyError:
            pass

        if bugstr == None:
            bugstr = retrieve_bug_html(id)
            if self.rep:
                self.rep.save(id, bugstr)
            
        try:
            return parse_bug(bugstr, id, 'Mozilla')
        except (AccessDenied, CantReadFile) as ex:
            logging.warn(ex)
            return None
