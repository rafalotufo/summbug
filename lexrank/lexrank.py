import numpy as np
import extractive_summary
from util.monads import option
from pagerank import pageRank
from functools import partial
from math import log
from bugreport_tokenizer import is_quotation, space_split, word_tokenize, space_tokenize
from text_sim import TextSimilarity, tfidf, norm
from mltk import ngram

def with_log(fn,a,b,title=None):
    x = fn(a,b)
    return option(x).map(lambda x: -log(x)).getOrElse(0) * x

def title_similarity(sim_fn, a, b, title):
    return sim_fn(title, b)

def boost_description(a, b, title=None):
    return a.id == b.id and a.id[0] == 0
    
def boost_with_polarity(has_polarity, sim_fn, a, b, title=None):
    '''
    - a comment with high similarity with another means that on refers to the other
    - if one of these comments has a negative or positive polarity sentence, then we can boost the
    votes for the sentences in the other comment
    '''
    assert a.thread_id == a.thread_id and a.thread_id != None, ('a.thread_id: %s, b.thread_id: %s' % (a.thread_id, b.thread_id))
    s = sim_fn(a,b)
    ## a comes after b and a is a polar sentence or comment
    if a.id[0] > b.id[0] and has_polarity(a.thread_id, a.id):
        return s
    else: 
        return 0

def with_threshold(fn, threshold, a,b, title=None):
    return 1 if fn(a,b) >= threshold else 0

def excl_sents_in_same_turn(sim_fn, a, b, title=None):
    '''a and b are sentences'''
    if a.id[0] != b.id[0]:
        return sim_fn(a, b, title)
    else:
        return 0

class BugSummarizer(object):
    def build_matrix(self, sentences, tokenized_sents, include_sent, tokenized_title):
        pass

    def tokenize_fn(self, text):
        pass
    
    def summarize(self, sentences, target_wc_perc, min_score, include_quot, damping_factor, error):
        return lexrank(sentences, self.build_matrix, target_wc_perc,
                       self.tokenize_fn, min_score, include_quot, damping_factor, error)

# FIXME: if title is not given, there is error. need to fix.
class LexrankSummarizer(object):
    def __init__(self):
        rank_type = 'contlexrank'
        similarity_fn = SimilarityFunctionFactory.build(
            rank_type=rank_type, sim='cosine', with_log=False,
              text_weight=0.5, title_weight=0.5, comment_polarity_predictor=None,
              sentence_length_threshold=16, boost_desc=True, desc_weight=None,
              include_sents_same_turn=True, sim_threshold=0)
        tokenize_fn = TokenizerFactory.build('word')
        self.summarize = LexrankFactory.build(
            similarity_fn, 
            SentenceScorerFactory.build(rank_type, similarity_fn),
            tokenize_fn,
            min_score=0, include_quot=False,
            error=0.05, damping_factor=0.85)
    
class TokenizerFactory(object):
    @staticmethod
    def build(tokenizer):
        if tokenizer == 'ngram':
            tokenize_fn = partial(ngram.tokenize, n=4)
        elif tokenizer == 'word':
            tokenize_fn = word_tokenize
        elif tokenizer == 'space':
            tokenize_fn = space_tokenize
        return tokenize_fn

class SentenceScorerFactory(object):
    @staticmethod
    def build(rank_type, similarity_fn):
        if rank_type == 'lexrank' or rank_type == 'contlexrank':
            score_sentences = partial(lexrank_matrix, similarity_fn=similarity_fn)
        return score_sentences

class SentenceSimilarityFactory(object):
    @staticmethod
    def build(sim):
        sim_fn = TextSimilarity(sim)
        return lambda a,b,title: sim_fn(a,b)
        
class SimilarityFunctionFactory(object):
    @staticmethod
    def build(rank_type='contlexrank', sim='cosine', with_log=False,
              text_weight=0.5, title_weight=0.5, comment_polarity_predictor=None,
              sentence_length_threshold=16, boost_desc=True, desc_weight=None,
              include_sents_same_turn=True, sim_threshold=0):
        '''
        rank_type: one of ['lexrank', 'contlexrank']
        sim: one of ['cosine', 'jaccard']
        text_weight:
        '''
        
        def linear_combination_similarity(sim_fns, weights, a, b, title=None):
            assert 0.99 < sum(weights) < 1.01 ## to avoid floating point precision issues
            return sum(sim_fn(a,b,title) * w for sim_fn, w in zip(sim_fns, weights))

        if rank_type in ['lexrank', 'contlexrank']:
            sim_fns = []
            weights = []

            if text_weight or title_weight or comment_polarity_predictor:
                base_sim_fn = SentenceSimilarityFactory.build(sim)
                
                if with_log:
                    base_sim_fn = partial(with_log, base_sim_fn)
            else:
                base_sim_fn = lambda a,b,title: 1.0 if a.id != b.id else 0
                weights.append(1)

            if sentence_length_threshold > 0:
                ## HOW DO WE MAKE POLARITY SELECT LONGER SENTENCES SUCH AS BELOW?
                def length_weight(fn, n, a,b,title=None):
                    return fn(a,b,title) * float(min(b.length, n))/n
                base_sim_fn = partial(length_weight, base_sim_fn, sentence_length_threshold)


            if text_weight:
                sim_fns.append(base_sim_fn)
                weights.append(text_weight)
                
            if title_weight:
                sim_fns.append(partial(title_similarity, base_sim_fn))
                weights.append(title_weight)

            ## this is ok to be here, since it is from one sentence to another
            if comment_polarity_predictor:
                comment_polarity_predictor = comment_polarity_predictor
                sentence_has_polarity = lambda thread_id, sid: comment_polarity_predictor.sentence_polarity(thread_id, sid)
                comment_has_polarity = lambda thread_id, sid: comment_polarity_predictor.comment_polarity(thread_id, sid[0])
                sim_fns.append(partial(boost_with_polarity, sentence_has_polarity, base_sim_fn))
                weights.append(1)
                sim_fns.append(partial(boost_with_polarity, comment_has_polarity, base_sim_fn))
                weights.append(1)

            if boost_desc:
                sim_fns.append(boost_description)
                weights.append(sum(weights))
            elif desc_weight:
                sim_fns.append(boost_description)
                weights.append(desc_weight)
                
            weights = [float(w)/sum(weights) for w in weights]
            base_sim_fn = partial(linear_combination_similarity, sim_fns, weights)
                
        if rank_type == 'lexrank':
            assert sim_threshold
            similarity_fn = partial(with_threshold, base_sim_fn, sim_threshold)
        elif rank_type == 'contlexrank':
            assert not sim_threshold
            similarity_fn = base_sim_fn
        else:
            similarity_fn = None

        if similarity_fn and not include_sents_same_turn:
            aux_sim_fn = similarity_fn
            similarity_fn = partial(excl_sents_in_same_turn, aux_sim_fn)
            
        return similarity_fn

class LexrankFactory(object):
    @staticmethod
    def build(similarity_fn, build_matrix, tokenize_fn, 
              min_score, include_quot,
              error=0.05, damping_factor=0.85):
        
        return partial(lexrank, build_matrix=build_matrix, 
                       tokenize_fn=tokenize_fn,
                       min_score=min_score, include_quot=include_quot,
                       error=error, damping_factor=damping_factor)

def lexrank_matrix(sentences, tokenized_sents, include_sent, similarity_fn=None, 
                   tokenized_title=None): 
    def build_similarity_matrix(objs, similarity_fn, include_obj, title=None):
        n = len(objs)

        M = np.zeros((n,n))
        for i in xrange(0,n):
            for j in xrange(0, n):
                if include_obj[j]:
                    M[i][j] = similarity_fn(objs[i], objs[j], title=title)

        return M

    if tokenized_title != None: ## need to discriminate [] and None
        tokenized_sents = [extractive_summary.Sentence((-1,0), tokenized_title)] + tokenized_sents
    objs = [s.map(text=lambda _:t) for s,t in zip(tokenized_sents, tfidf(s.text for s in tokenized_sents))]
    for obj in objs:
        obj.norm = norm(obj.text.itervalues())
    if tokenized_title != None: ## need to discriminate [] and None
        title_obj = objs[0]
        objs = objs[1:]
    else:
        title_obj = None
    G = build_similarity_matrix(objs, similarity_fn, include_sent, title_obj)
    return G
    
def lexrank(sentences, build_matrix, target_wc_perc, tokenize_fn, min_score,
            include_quot, damping_factor=0.85, error=0.001,
            title=None):
    assert isinstance(min_score, (int, float)), 'min_score needs to be float, not %s' % type(min_score)
    assert isinstance(include_quot, bool)

    include_sent = [(include_quot or not is_quotation(s.text)) and \
                    not extractive_summary.exclude_sentence(s.text) for s in sentences]

    tokenized_sents = [s.map(text=lambda t:list(tokenize_fn(t)),
                             length=lambda t:len(space_split(s.text)))
                             for s in sentences]
    tokenized_title = tokenize_fn(title) if title != None else None

    M = build_matrix(sentences, tokenized_sents, include_sent, 
                     tokenized_title=tokenized_title)

    scores = pageRank(M, s=damping_factor, maxerr=error)
    assert len(scores) == len(sentences)
                
    ## normalize scores: 1 is equal to average page rank
    ## round to avoid float precision issues
    sentence_scores = [round(s*len(tokenized_sents), 5) for s in scores]
    sentence_wc = extractive_summary.count_words(tokenized_sents)
    summary = extractive_summary.build_summary(sentences, sentence_scores, sentence_wc, 
                                               target_wc_perc, min_score)
    return summary, sentence_wc

