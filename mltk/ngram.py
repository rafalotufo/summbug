#!/usr/bin/env python

import itertools

def ngrams(word, n):
    word = ' %s ' % word
    if len(word) <= n: return word
    return [word[i:i+n] for i in range(len(word) - n + 1)]
    
def tokenize(text, split=lambda t: t.split(), n=4):
    return itertools.chain.from_iterable(ngrams(w.lower(),n) for w in split(text))
