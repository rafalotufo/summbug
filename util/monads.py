class option(object):
    def __init__(self, some):
        self.some = some

    def getOrElse(self, v):
        if self.some: return self.some
        else: return v

    def map(self, f):
        if self.some: return option(f(self.some))
        else: return Empty

Empty = option(None)

def head(l):
    """return option of head of list"""
    if l: return option(l[0])
    else: return Empty

def empty_if(obj, is_empty):
    if is_empty: return Empty
    else: return option(obj)

class Box(object):
    def __init__(self, obj=None, is_failure=False):
        '''
        FullBox: obj != None, failure == False
        EmptyBox: obj == None, failure == False
        Failure: obj == None, failure == True
        '''
        assert obj or not is_failure, (obj, is_failure)  # is_failure -> obj
        self.obj = obj
        self.is_failure = is_failure
        self.is_full = not self.is_failure and self.obj

    def map(self, f):
        if self.is_full:
            return option(f(self.obj))
        else:
            raise Exception('Box is empty')

    def getOrElse(self, v):
        if self.is_full:
            return self.obj
        else:
            return v

def tryo(f, *args, **kwargs):
    try:
        return Box(obj=f(*args, **kwargs))
    except Exception as e:
        return Box(obj=e, is_failure=True)
        
