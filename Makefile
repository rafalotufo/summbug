LEX_DIR=~/projects/bug-summary-main/bug-summary/python/
BR_DIR=~/projects/bug-reports/bugreports/
UTIL_DIR=~/projects/python-util/util/
MLTK_DIR=~/projects/mltk/src/mltk/

BR_FILES=$(addprefix $(BR_DIR), bug_retriever.py launchpad_bugs.py mozilla_bugs.py \
	__init__.py chrome_bugs.py debian_bugs.py bugs.py db.py)
BR_TARGETS=$(addprefix bugreports/, $(notdir $(BR_FILES)))

LEX_FILES=$(addprefix $(LEX_DIR), __init__.py lexrank.py bugreport_tokenizer.py \
	extractive_summary.py pagerank.py text_sim.py)
LEX_TARGETS=$(addprefix lexrank/, $(notdir $(LEX_FILES)))

UTIL_FILES=$(addprefix $(UTIL_DIR), __init__.py monads.py lists.py)
UTIL_TARGETS=$(addprefix util/, $(notdir $(UTIL_FILES)))

MLTK_FILES=$(addprefix $(MLTK_DIR), __init__.py ngram.py)
MLTK_TARGETS=$(addprefix mltk/, $(notdir $(MLTK_FILES)))

run: $(LEX_TARGETS) $(BR_TARGETS) $(UTIL_TARGETS) $(MLTK_TARGETS)
	dev_appserver.py -p 8083 .

$(LEX_TARGETS): $(LEX_FILES)
	test -d $(dir $@) || mkdir $(dir $@)
	cp $(addprefix $(LEX_DIR), $(notdir $@)) $@

$(BR_TARGETS): $(BR_FILES)
	test -d $(dir $@) || mkdir $(dir $@)
	cp $(addprefix $(BR_DIR), $(notdir $@)) $@

$(UTIL_TARGETS): $(UTIL_FILES)
	test -d $(dir $@) || mkdir $(dir $@)
	cp $(addprefix $(UTIL_DIR), $(notdir $@)) $@

$(MLTK_TARGETS): $(MLTK_FILES)
	test -d $(dir $@) || mkdir $(dir $@)
	cp $(addprefix $(MLTK_DIR), $(notdir $@)) $@