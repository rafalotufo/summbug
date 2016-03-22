import itertools, os, shutil
from util.monads import option
import editdist

class Sentence(object):
    def __init__(self, id, text, thread_id=None, length=None, norm=None):
        self.id = id
        self.text = text
        self.thread_id = thread_id
        self.length = length
        self.norm = norm

    def map(self, **kwargs):
        def ident(a): return a
        id = kwargs.get('id', ident)(self.id)
        text = kwargs.get('text', ident)(self.text)
        thread_id = kwargs.get('thread_id', ident)(self.thread_id)
        length = kwargs.get('length', ident)(self.length)
        norm = kwargs.get('norm', ident)(self.norm)
        return Sentence(id, text, thread_id, length, norm)
        
    def __str__(self):
        return 'Sentence(%s, %s, %s, %s)' % (str(self.id), str(self.text), str(self.thread_id), str(self.length))

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        else:
            return self.__dict__ == other.__dict__

class MeanCalculator(object):
    def __init__(self, keys):
        self.keys = keys
        self.scores_sum = dict((key, 0) for key in keys)
        self.n = 0

    def add(self, item):
        for k in self.keys:
            self.scores_sum[k] = self.scores_sum[k] + option(item[k]).getOrElse(0)
        self.n += 1

    def mean(self, precision=2):
        return [(k,round(float(v)/self.n, precision)) for k,v in self.scores_sum.items()]
    
# can delete this. new one in summary_writer.py
def save_summary_file(filename, sentences, is_in_summary):
    '''Save summary file

    filename - file to write to
    sentences - list of sentences in bug report
    is_selected - list of boolean if the sentence is in summary'''
    with open(filename, 'w') as f:
        turn = None
        for s,include in zip(sentences, is_in_summary):
            if turn != None and turn != s.id[0]:
                f.write('\n')
            f.write(s.text.encode('ascii', 'ignore') + '\n')
            turn = s.id[0]

def precision(predicted_sents, annotated_sents, min):
    annotated_sents = dict((k,len(v)) for k,v in annotated_sents.items())
    if predicted_sents:
        return float(len([s for s in predicted_sents if annotated_sents.get(s, 0) >= min])) / len(predicted_sents)
    else:
        return None

def recall(predicted_sents, annotated_sents, min):
    annotated_sents = dict((k,len(v)) for k,v in annotated_sents.items())
    return float(len([s for s in predicted_sents if annotated_sents.get(s, 0) >= min])) / \
        len([a for a in annotated_sents.values() if a >= min])

def fscore(predicted_sents, annotated_sents, min):
    if predicted_sents:
        p = precision(predicted_sents, annotated_sents, min)
        r = recall(predicted_sents, annotated_sents, min)
        if p + r:
            return 2 * p * r / (p + r)
        else:
            return 0
    else:
        return None

def pyramid_precision(predicted_sents, annotated_sents):
    '''Calculates pyramid precision, as explained in "Generating Overview Summaries of Ongoing Email Thread Discussions"

    predicted_sents - list of ids of predicted sentences
    annotated_sents - dict of ids of sentences, and number of 
                      times they were linked by annotators
    '''
    ## For each generated summary of a given length, we count
    ## the total number of times the sentences in the summary
    ## were linked by annotators
    annotated_sents = dict((k,len(v)) for k,v in annotated_sents.items())
    links = reduce(lambda a,b: a + annotated_sents.get(b,0), predicted_sents, 0)

    ## then calculate, for the best summary of size n (the top n most linked sentences),
    ## the total number of links they have received
    if predicted_sents:
        MAX = 0
        for s,_ in zip(sorted(annotated_sents.values(), reverse=True), predicted_sents):
            MAX += s
            
        return float(links) / MAX
    else:
        return None

def count_words(sentences):
    sentence_word_count = {}
    for s in sentences:
        if s.text:
            for w in s.text:
                sentence_word_count[s.id] = sentence_word_count.get(s.id, 0) + 1
        else:
            sentence_word_count[s.id] = 0        
    return sentence_word_count

sentences_to_exclude = {'(No comment was entered for this change.)'}    
def exclude_sentence(s, sentences_to_exclude=sentences_to_exclude, min_dist=0.1):
    return any(float(editdist.distance(s, ex))/len(ex) < min_dist  for ex in sentences_to_exclude)

def build_summary(sentences, sentence_probs, sentence_wc, target_wc_perc, min_score):
    '''Builds the summarized email text, based on the sentence probabilities'''
    def find_sentences(sentences, sentence_probs, sentence_wc):
        word_count = 0
        for p,s in sorted(itertools.izip(sentence_probs, sentences), reverse=True):
            assert isinstance(p, (int, long, float)), ('scores must be float, not %s' % type(p))
            if word_count >= target_wc_perc * total_wc:
                return
            elif p >= min_score:
                word_count += sentence_wc[s.id]
                yield s

    assert isinstance(min_score, (int, long, float)), ('min_score must be numeric, not %s' % type(min_score))
    total_wc = sum(sentence_wc.values())
    selected_sentences = set(s.id for s in find_sentences(sentences, sentence_probs, sentence_wc))
    for s in sentences:
        if s.id in selected_sentences and not exclude_sentence(s.text):
            yield  s 

def evaluate(summary, sentences, annotated_sents, sentence_wc, min, rouge_params=None):
    selected_ids,selected_text = zip(*[(s.id,s.text) for s in summary])

    num_words_total = sum(sentence_wc.values())
    words_selected = float(sum(sentence_wc[sid] for sid in selected_ids)) / num_words_total
    num_sents_total = len(sentences)
    sents_selected = float(len(selected_ids)) / num_sents_total

    def build_ref_summaries(ref, sentences):
        sentences_by_id = dict((s.id, s) for s in sentences)
        summaries = {}
        for sid,refs in annotated_sents.items():
            for r in refs:
                summaries.setdefault(r, []).append(sentences_by_id[sid].text)
        return summaries.items()
    
    if rouge_params != None:
        import rouge
        from rouge import Summary as S

        r = rouge.Rouge()
        for ref,ref_summary in build_ref_summaries(annotated_sents, sentences):
            r.add_ref_summary(S('?', str(ref), ref_summary))
        r.add_peer_summary(S('?', '?', selected_text))
        eval_dir = '.rouge-eval'
        os.mkdir(eval_dir)
        try:
            r.create_data(eval_dir)
            rouge_results = rouge.run_rouge(rouge_params, eval_dir)
            rouge_results = rouge.parse_results(rouge_results.split('\n'))
        finally:
            shutil.rmtree(eval_dir)
    
    else:
        rouge_results = None
    
    return {'py_prec': round(pyramid_precision(selected_ids, annotated_sents),2),
            'prec': round(precision(selected_ids, annotated_sents, min),2),
            'rec': round(recall(selected_ids, annotated_sents, min),2),
            'fscore': round(fscore(selected_ids, annotated_sents, min),2),
            'prec1': round(precision(selected_ids, annotated_sents, min=1),2),
            'rec1': round(recall(selected_ids, annotated_sents, min=1),2),
            'fscore1': round(fscore(selected_ids, annotated_sents, min=1),2),
            'sentences': sentences,
            'predicted_in_summary': [s.id in selected_ids for s in sentences],
            'is_in_summary': [len(annotated_sents.get(s.id, [])) >= min for s in sentences],
            'words_selected': round(words_selected,2),
            'num_words_total': num_words_total,
            'sents_selected': round(sents_selected,2),
            'num_sents_total': num_sents_total,
            'rouge': rouge_results}
                 
def filename_suffix(**kwargs):
    return '-'.join('%s-%s' % (k,str(v)) for k, v in sorted(kwargs.items()))
    
