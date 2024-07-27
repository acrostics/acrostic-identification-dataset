import numpy as np
import matplotlib.pyplot as plt
import pylcs
import re
import os
import argparse


class Language:
    all = []

    def __init__(self, code):
        Language.all.append(code)
        self.code = code


EN = Language("EN")
LA = Language("LA")
RU = Language("RU")
FR = Language("FR")


def format(line, lang):
    line = line.lower()
    if lang == EN.code:
        line = re.sub("'", "", line)
        line = re.sub(r"[^a-z ]", " ", line)
    elif lang == LA.code:
        line = re.sub(r"[^a-z ]", " ", line)
        line = re.sub(r"v", "u", line)
        line = re.sub(r"j", "i", line)
    elif lang == RU.code:
        line = re.sub(r"[^ЁёѣiА-яaeopxc ]", " ", line)
        line = re.sub(r"[aA]", "а", line)
        line = re.sub(r"[Pp]", "р", line)
        line = re.sub(r"[xX]", "х", line)
        line = re.sub(r"[cC]", "с", line)
        line = re.sub(r"[oO]", "о", line)
        line = re.sub(r"[ёѣEe]", "е", line)
        line = re.sub(r"[йi]", "и", line)
        line = re.sub(r"[ьъ]", "", line)
    elif lang == FR.code:
        # Replace accented characters and ligatures
        line = re.sub(r"[àâä]", "a", line)
        line = re.sub(r"[éèêë]", "e", line)
        line = re.sub(r"[îï]", "i", line)
        line = re.sub(r"[ôö]", "o", line)
        line = re.sub(r"[ùûü]", "u", line)
        line = re.sub(r"ç", "c", line)
        line = re.sub(r"œ", "oe", line)
        line = re.sub(r"æ", "ae", line)
        line = re.sub(r"j", "i", line)
        line = re.sub(r"v", "u", line)
        line = re.sub(r"'", "", line)  # Remove apostrophes
        line = re.sub(r"[^a-zA-Z ]", " ", line)  # Replace non-letter characters with space
    return line


def is_file(path):
    if os.path.isfile(path):
        return path
    raise argparse.ArgumentTypeError(f"Could not find file "
                                     f"({path} does not exist)")


def is_path(path):
    if os.path.isfile(path) or os.path.isdir(path):
        return path
    raise argparse.ArgumentTypeError(f"{path} is not a valid path")


def find_LCS(s1, s2):
    res = pylcs.lcs_string_idx(s1, s2)
    return ''.join([s2[i] for i in res if i != -1])


def get_truth(truth_file, lang):
    results = [line.strip("\n").split("\t") for line in open(truth_file).readlines()[1:]]
    results_dict = {}
    for result in results:
        if 'n' in result[0] or 'o' in result[0] or '2' in result[0] or '4' in result[0] or 't' in result[0] or 'i' in result[0] or '3' in result[0] or 'e' in result[0] or 'w' in result[0]:
            continue
        if result[2] not in results_dict:
            results_dict[result[2]] = []
        results_dict[result[2]].append(re.sub(" ", "", format(result[1], lang)))
    return results_dict


def get_recall(filename, truth_file, lang, log=False):
    results_dict = get_truth(truth_file, lang)
    output = open(filename).readlines()[1:]
    output = [line.strip("\n").split("\t") for line in output]
    output.reverse()
    recall = np.zeros(len(output))
    tp = 0
    all_tp = sum(len(results_dict[k]) for k in results_dict.keys())
    for k in range(len(output)):
        title, acrostic, _, _, _, cluster, _, _, prefix, postfix, _ = output[k]
        query_full = prefix + cluster + postfix
        query = re.sub(' ', '', format(query_full, lang))
        to_remove = []
        if title in results_dict:
            for result in results_dict[title]:
                if result in query or len(find_LCS(result, query)) >= 5:
                    if log:
                        print(f"Hit {result}")
                    tp += 1
                    to_remove.append(result)
            for result in to_remove:
                results_dict[title].remove(result)
        if not to_remove and log and k < 2000:
            print(f"Miss {acrostic} ({query_full}) in {title}")
        # if log:
        #     print(f"k={k},\trecall={tp/all_tp}")
        recall[k] = tp/all_tp
    if log:
        for title in results_dict:
            if len(results_dict[title]) > 0:
                for result in results_dict[title]:
                    print(f"Cannot find {result} in {title}")
    return recall


# recall100 = get_recall("output_sorted_model_100.tsv", "results.txt", log=False)
# recall300 = get_recall("output_sorted_model_300.tsv",  "results.txt",log=False)
# recall900= get_recall("output_sorted_model_900.tsv", "results.txt", log=False)
# recall2700 = get_recall("output_sorted_model_2700.tsv", "results.txt", log=False)
# recall8100 = get_recall("output_sorted_model_8100.tsv",  "results.txt",log=False)
# recall24300 = get_recall("output_sorted_model_24300.tsv",  "results.txt",log=False)
recall72900 = get_recall("../outputFr.tsv",  "../evaluation/frwikisource.tsv", lang="FR", log=True)

# recall24300Russian = get_recall("output_russian.tsv",  "resultsRussian.tsv", log=True, cyrillinc=True)

fig, ax = plt.subplots(layout='constrained')

""""
plt.plot(np.arange(len(recall100)), recall100, label="100 token LM", linestyle="-", linewidth=3)
plt.plot(np.arange(len(recall300)), recall300, label="300 token LM", linestyle=":", linewidth=3)
plt.plot(np.arange(len(recall900)), recall900, label="900 token LM", linestyle="--", linewidth=3)
plt.plot(np.arange(len(recall2700)), recall2700, label="2700 token LM", linestyle="-.", linewidth=3)
plt.plot(np.arange(len(recall8100)), recall8100, label="8100 token LM", linestyle="-", linewidth=3)
plt.plot(np.arange(len(recall24300)), recall24300, label="24300 token LM", linestyle=":", linewidth=3)
"""
plt.plot(np.arange(len(recall72900)), recall72900, label="72900 token LM", linestyle="--", linewidth=3)


# plt.plot(np.arange(len(recall24300)), recall24300, label="English, 24300 token LM", linestyle=":", linewidth=3)
# plt.plot(np.arange(len(recall24300Russian)), recall24300Russian, label="Russian, 24300 token LM", linestyle=":", linewidth=3)

plt.legend(loc='upper left', fontsize=36)
ax.set_ylabel('Recall', fontsize=50)
ax.set_xlabel('# of results', fontsize=50)
# one dot for each unit
ax.tick_params(axis='x', labelsize=36)  # Adjust as needed for the x-axis tick labels
ax.tick_params(axis='y', labelsize=36)  # Adjust as needed for the y-axis tick labels
fig.set_size_inches(24, 16)
ax.set_xscale('log')
plt.show()