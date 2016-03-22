import re, random
from util.monads import option, head
from nltk import stem, tokenize as nltk_tokenize

eng_words = set(w.strip() for w in open('english-words.txt').readlines())

def lower_and_stem(s):
    return stem.PorterStemmer().stem_word(s.lower())

def space_split(s):
    return s.split()

def word_split(s):
    t = nltk_tokenize.RegexpTokenizer(r'[\w-]+(\.[\w-]+)*')
    return t.tokenize(s)

def word_tokenize(s):
    return tokenize(word_split, lower_and_stem, s)

def space_tokenize(s):
    return tokenize(space_split, lower_and_stem, s)

def tokenize(split, post_process, s):
    return map(lambda si: post_process(si), split(s))

def is_quotation(s):
    return head(s.strip()).getOrElse('') == '>'

def perc_english_words(words, eng_words):
    if not words:
        return 0
    return float(reduce(lambda count,w: count + (1 if w in eng_words else 0), words, 0)) / len(words)

def is_english_sentence(line, eng_words, min=0.5):
    words = line.split()
    return perc_english_words(words, eng_words) > min

## FIXME: reimplement!
## need to better handle structures, blocks of text:
## - lists do we include the entire list of not?
## - something that has a header (specially a list)
## - blocks of code
## - blocks of diagnostic information
## - quotes
## - signatures (automatically ignore them)

## we can still show only some parts of a block, but
## we can improve on the presentation, such as showing the
## header, and '...' that there is more info there.
## maybe we should include the first and last sentence of every
## paragraph that has an included sentence

# Versions of the packages jed depends on: (HEADER)
# ...
# ii  slang1         1.4.4-3        The S-Lang programming library - runtime ver
def split_sentences(text):
    '''
    for every line break in text, we need to decide:
    - if the line break finishes a sentence or if next line should
      be joined with the current line
    then, for every block of lines, we need to decide:
    - how many sentences within that block
    '''
    def is_bullet(line):
        return re.match('\s*[\-\*]|\d+[:\.\-\)]|\(\d+\)', line) != None

    def split_sents(line):
        def version_replace(matchobj):
            key = ('@version-replace:%f:version-replace@' % random.random()).replace('.', '_')
            versions[key] = matchobj.group(0)
            return key

        def replace_version(line):
            def rv(matchobj):
                return versions[matchobj.group(0)]
            return re.sub(r'(@version-replace:.+?:version-replace@)', rv, line)
        
        versions = {}
        i = 0
        ## ignores '.' char when used in google.com, 12.10.1, etc
        line = re.sub(r'(e\.g\.)|(i\.e\.)', version_replace, line)  ## needs to come first
        line = re.sub(r'(\w+(?:\.\w+)+)', version_replace, line) 
        a = re.split('([\.\?!;]+\s)', line)
        if len(a) == 1:
            return [replace_version(a[0])]
        else:
            if not a[-1]:
                a = a[:-1]
            return [replace_version(a[i]+option(i < len(a) - 1).map(lambda _: a[i+1]).getOrElse(''))
                    for i,_ in enumerate(a) if not i % 2]
    
    def split_sents_in_block(block):
        for sent in split_sents(' '.join(block) + '\n'):
            yield sent
                
    def split_blocks(text):
        block = []
        on_bullet = False
        for line in re.split('\n', text):
            ## start of line shows end of previous block
            if not line.strip():
                yield ('bullet' if on_bullet else 'block1'),block
                block = []
                on_bullet = False
            elif is_bullet(line):
                if block:
                    yield ('bullet' if on_bullet else 'block2'),block
                block = [line]
                on_bullet = True
                if len(line) < 60:
                    yield 'bullet',block
                    on_bullet = False
                    block = []
            ## end of line shows end of current block
            elif line[-1] in '!?:;.)':
                block += [line]
                yield ('bullet' if on_bullet else 'block3'),block
                block = []
                on_bullet = False
            elif len(line) < 60 or not is_english_sentence(line, eng_words):
                block += [line]
                yield ('bullet' if on_bullet else 'block4'),block
                block = []
                on_bullet = False
            else:
                block += [line]
                on_bullet = False

    if not text:
        return
    for type,block in split_blocks(text):
        if type == 'bullet':
            yield ' '.join(block) + '\n'
        else: 
            for sent in split_sents_in_block(block):
                yield sent
