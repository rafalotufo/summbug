#!/usr/bin/env python

from launchpadlib.launchpad import Launchpad
import json, datetime, logging
from bugreports import bugs
import bug_retriever
from util.monads import option

default_launchpad_folder = '/Users/rlotufo/projects/bug-reports/launchpad/'

def login():
    cachedir = "/Users/rlotufo/.launchpadlib/cache/"
    lpad = Launchpad.login_anonymously('just testing', 'production', cachedir)
    return lpad

def to_ascii(text):
    if isinstance(text, basestring):
        return text.encode('ascii', 'ignore')
    else:
        return text

def retrieve_owner(lpad, url):
    return lpad.load(url).name

def retrieve_comments(lpad, url):
    for i,c in enumerate(lpad.load(url).entries):
        c['date_created'] = c['date_created'].split('+')[0].split('.')[0] # take first part before '.'
        yield bugs.Comment(i, retrieve_owner(lpad, c['owner_link']), 
                      datetime.datetime.strptime(c['date_created'], '%Y-%m-%dT%H:%M:%S'),
                      c['content'], title=c['subject']) 

def retrieve_bug(lpad, number):
    '''lpad should have been retrived using login() function'''
    try:
        bug = lpad.bugs[number]
        status = [t.status for t in bug.bug_tasks]
    except KeyError:
        logging.warning('Could not retrieve bug report %s', str(number))
        return None

    comments = list(retrieve_comments(lpad, bug.messages_collection_link))
    #    owner = retrieve_owner(lpad, bug.owner_link)
    return bugs.BugReport('Launchpad', bug.id, bug.title, bug.description, 
                                               retrieve_owner(lpad, bug.owner_link), 
                                                                    bug.date_created, comments, status=status)
        # return {'bug': bug.to_json_obj(), 
        #     'status': status, 
        #     'comments': [c.to_json_obj() for c in comments], 
        #     'owner': owner}

class LaunchpadBugRetriever(object):
    def __init__(self, folder=default_launchpad_folder):
        '''rep is instance of BugRepository'''
        self.rep = bug_retriever.BugRepository(folder, ext='json') if folder else None
        self.lpad = login()

    def retrieve_bug(self, id, from_rep=True):
        if self.rep and from_rep and id in self.rep:
            bugstr = self.rep.read(id)
        else:
            bugstr = option(retrieve_bug(self.lpad, id)).map(lambda b: b.to_json_obj()).getOrElse(None)
            if self.rep:
                self.rep.save(id, json.dumps(bugstr))

        # bug = bugstr['bug']
        # comments = bugstr['comments']
        # status = bugstr['status']
        # owner = bugstr['owner']
        # return bugs.BugReport('Launchpad', bug['id'], bug['title'], bug['desc'], 
        #              owner, 
        #              bug['date_created'], comments, status=status)
        return bugs.BugReport.from_json(bugstr)
