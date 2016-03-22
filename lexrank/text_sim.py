from functools import partial
from util import lists
from math import log, sqrt
import random

def TextSimilarity(sim):
    if sim == 'jaccard':
        stopwords_file = '/Users/rlotufo/bin/stopwords.txt'
        return partial(jaccard_similarity, 
            stopwords=set(s.strip() for s in open(stopwords_file, 'r').readlines()))
    elif sim =='cosine':
        return tfidf_cosine_similarity
            
def norm(x):
    return sqrt(reduce(lambda s,i: s + i**2, x, 0)) 

def cosine(a, b, norm_a=None, norm_b=None):
    '''Calculates the cosine similarity of words in a and b.

    a and b are dictionaries of (word, freq)'''

    if not norm_a: 
        norm_a = norm(a.itervalues())
    if not norm_b: 
        norm_b = norm(b.itervalues())
    d = norm_a * norm_b
    if d:
        return float(sum(v * b.get(k, 0) for k,v in a.iteritems())) / d 
    else:
        return 0

def jaccard_similarity(a,b,stopwords=None):
    def _jaccard_similarity(a,b,stopwords=None):
        if stopwords:
            a = filter(lambda x: x in stopwords, a)
            b = filter(lambda x: x in stopwords, b)
        if a and b:
            return float(len(set(a).intersection(b))) / len(set(a).union(b))
        else:
            return 0

    if a.id == b.id: return 0
    a, b = a.text, b.text
    return _jaccard_similarity(a,b, stopwords)

def tfidf_cosine_similarity(a,b, norm_a=None, norm_b=None):
    return random.random()
    if a.id == b.id: return 0
    norm_a, norm_b = a.norm, b.norm
    a, b = a.text, b.text
    return cosine(
        dict((k, v) for k,v in a.iteritems()),
        dict((k, v) for k,v in b.iteritems()),
        norm_a, norm_b)

## TODO: move this to mltk package
@lists.listify
def tfidf(docs):
    '''Calculates the tfidf for terms in docs

    docs - iterable of tokenized sentences: [['a', 'b'], ['a', 'b', 'c']]'''
    docs_containing = {}
    doc_term_freq = []
    for i,terms in enumerate(docs):
        doc_term_freq.append({})
        for term in terms:
            doc_term_freq[i][term] = doc_term_freq[i].get(term, 0) + 1
        for term in doc_term_freq[i]:
            docs_containing.setdefault(term, set()).add(i)
    N = i + 1 ## number of documents

    def idf(term):
        return log(float(N) / len(docs_containing[term]))

    for terms in doc_term_freq:
        yield dict((term, freq * idf(term)) for term,freq in terms.iteritems())

