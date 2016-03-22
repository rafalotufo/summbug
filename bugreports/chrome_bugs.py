import db, bugs

chrome_db = db.BugReportDB(db.chrome_db, db.chrome_today)

def retrieve_bug(id):
    def to_comment(c):
        return bugs.Comment(c.num,c.author,c.date,c.text)
    bug = chrome_db.find_by_id(id)
    try:
        bug = bug.next()
        return bugs.BugReport('Chrome', int(bug.id), bug.title, bug.desc, bug.author, bug.date,
                              [bugs.Comment(0, bug.author, bug.date, bug.desc)] + map(to_comment, bug.comments),
                              followers = bug.followers, status = bug.status, 
                              close_date=bug.close_date)
    except StopIteration:
        return None
