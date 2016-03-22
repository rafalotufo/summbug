
from functools import wraps
import itertools, sys, random

def listify(gen):
    "Convert a generator into a function which returns a list"
    def patched(*args, **kwargs):
        return list(gen(*args, **kwargs))
    return patched

def setify(gen):
    def patched(*args, **kwargs):
        return set(gen(*args, **kwargs))
    return patched

def dictate(func):
    @wraps(func)
    def patched(*args, **kwargs):
        return dict(func(*args, **kwargs))
    return patched

@listify
def listify_groups(gs):
    for g,s in gs:
        yield (g, list(s))

def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(itertools.islice(iterable, n))

class EnumerateIter(object):
    def __init__(self, it, n=1):
        self.__it = it
        self.i = 0
        self.n = n

    def __iter__(self):
        return self

    def next(self):
        try:
            if self.i % self.n == 0:
                print >> sys.stderr, '\rRow %d      ' % self.i,
            self.i += 1
            return self.__it.next()
        except Exception as e:
            print >> sys.stderr, '\n'
            raise e
        
    def __getattr__(self,name):
        return self.__it.getattr(name)

def sample_iter(it, prob=100):
    '''it is iter type
    prob is prob of each independent trial'''
    def next_countdown(n):
        return int(random.random() * n)
    
    countdown = next_countdown(prob)
    for item in it:
        if countdown == 0:
            countdown = next_countdown(prob)
            yield item
        else:
            countdown -= 1

