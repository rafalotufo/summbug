from functools import partial

class BugCache(object):
    def __init__(self):
        self.cache = {}
        
    def add_to_cache(self, project, bug_id, bug):
        self.cache[(project,bug_id)] = bug

    def get_from_cache(self, project, bug_id):
        return self.cache[(project,bug_id)]

    def is_cached(self, project, bug_id):
        return (project,bug_id) in self.cache
    
def with_cache(retrieve, cache, project, bug_id):
    if cache.is_cached(project, bug_id):
        return cache.get_from_cache(project, bug_id)
    else:
        bug = retrieve(project, bug_id)
        cache.add_to_cache(project, bug_id, bug)
        return bug

def retrieve(project, bug_id):
    if project.lower() == 'debian':
        from bugreports import debian_bugs
        return debian_bugs.DebianBugRetriever(None).retrieve_bug(bug_id)
    elif project.lower() == 'mozilla':
        from bugreports import mozilla_bugs
        from bugreports.mozilla_bug_parser import parse_bug
        return parse_bug(mozilla_bugs.retrieve_bug_html(bug_id), bug_id, project)

def cached_retriever():
    return partial(with_cache, retrieve, BugCache())
