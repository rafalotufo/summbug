import os, re

def get_retriever(project, **kwargs):
    if project == 'Launchpad':
        import launchpad_bugs
        return launchpad_bugs.LaunchpadBugRetriever().retrieve_bug
    elif project == 'Chrome':
        import chrome_bugs
        return chrome_bugs.retrieve_bug
    elif project == 'Mozilla':
        import mozilla_bugs
        return mozilla_bugs.MozillaBugs(**kwargs).retrieve_bug
    elif project == 'Debian':
        import debian_bugs
        return debian_bugs.DebianBugRetriever().retrieve_bug
    else:
        raise Exception('Project "%s" unknown' % project)

class BugRetriever(object):
    def __init__(self, project, **kwargs):
        self.retrieve_bug = get_retriever(project, **kwargs)

class BugRepository(object):
    def __init__(self, folder, ext='html'):
        '''folder is where to save bugs'''
        self.folder = folder
        self.ext = ext
        self.__init_index(folder)
        
    def __init_index(self, folder):
        self.__index = set()
        for fn in os.listdir(self.folder):
            m = re.match('(\d+)\.%s' % self.ext, fn)
            if m:
                self.__index.add(m.group(1))

    def __contains__(self, id):
        return id in self.__index

    def __filename(self, id):
        return '%s/%s.%s' % (self.folder, id, self.ext)

    def save(self, id, bug):
        with open(self.__filename(id), 'w') as f:
            f.write(bug)

    def read(self, id):
        with open(self.__filename(id), 'r') as f:
            return f.read()
