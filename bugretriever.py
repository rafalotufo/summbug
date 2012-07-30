def retrieve(project, bug_id):
    if project.lower() == 'debian':
        from bugreports import debian_bugs
        return debian_bugs.DebianBugRetriever(None).retrieve_bug(bug_id)
