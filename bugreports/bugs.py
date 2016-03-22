import datetime

datetime_format = '%Y-%m-%d %H:%M:%S'

class BugReport(object):
    def __init__(self, project, id, title, desc, reporter, open_date, comments, **attrs):
        self.project = project
        self.id = id
        self.title = title
        self.desc = desc
        self.reporter = reporter
        assert(type(open_date) == datetime.datetime)
        self.open_date = open_date
        self.comments = comments
        self.attrs = attrs

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.to_json_obj() == other.to_json_obj()
        else:
            return False

    def to_json_obj(self):
        r = self.__dict__
        r['open_date'] = r['open_date'].strftime(datetime_format)
        r['comments'] = [c.to_json_obj() for c in r['comments']]
        return r

    @staticmethod
    def from_json(j):
        if j:
            j['comments'] = [Comment.from_json(c) for c in j['comments']]
            j['open_date'] = datetime.datetime.strptime(j['open_date'], datetime_format)
            return BugReport(**j)
    
class Comment(object):
    def __init__(self, number, author, date, text, **attrs):
        self.number = number
        self.author = author
        assert(type(date) == datetime.datetime)
        self.date = date
        self.text =text
        self.attrs = attrs
        
    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def to_json_obj(self):
        r = self.__dict__
        r['date'] = r['date'].strftime(datetime_format)
        return r

    @staticmethod
    def from_json(j):
        j['date'] = datetime.datetime.strptime(j['date'], datetime_format)
        return Comment(**j)
