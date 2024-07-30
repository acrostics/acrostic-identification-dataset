import numpy as np
import matplotlib.pyplot as plt
import pylcs
import re
import os
import argparse
import sys


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


def get_true_labels(truth_file, lang):
    results = [line.strip("\n").split("\t") for line in open(truth_file).readlines()[1:]]
    true_labels = []
    join_with_previous = False  # cluster acrostics that are split into multiple files together to count them as one
    for result in results:
        does_not_count_towards_recall = False
        for label in 'no23468itwe':
            if label in result[0]:
                does_not_count_towards_recall = True
                break
        if does_not_count_towards_recall:
            join_with_previous = join_with_previous and 's' in result[0]
            continue
        acrostic = re.sub(" ", "", format(result[1], lang))
        page = result[2]
        if not join_with_previous:
            true_labels.append([(acrostic,page)])
        else:
            true_labels[-1].append((acrostic,page))
        join_with_previous = 's' in result[0]
    true_labels = [tuple(x) for x in true_labels]
    return true_labels


def get_recall(filename, truth_file, lang, log=False):
    true_labels = get_true_labels(truth_file, lang)
    output = open(filename).readlines()[1:]
    output = [line.strip("\n").split("\t") for line in output]
    output.reverse()
    recall = np.zeros(len(output))
    tp = 0
    all_tp = len(true_labels)
    removed = []
    for k in range(len(output)):
        title, candidate, _, _, _, cluster, _, _, prefix, postfix, _ = output[k]
        query_full = prefix + cluster + postfix
        query = re.sub(' ', '', format(query_full, lang))
        to_remove = []
        for label in true_labels:
            for acrostic, page in label:
                if title == page and (acrostic in query or len(find_LCS(acrostic, query)) >= 5):
                    if label not in to_remove:
                        tp += 1
                        to_remove.append(label)
        for label in to_remove:
            if log:
                print(f"Hit {label[0][0]}, k={k}, tp={tp}, all_tp={all_tp}, recall={tp / all_tp}")
            true_labels.remove(label)
            removed.append(label)
        """if not to_remove and log and k < 3000:
            already_counted = False
            for label in removed:
                for acrostic, page in label:
                    if title == page and (acrostic in query or len(find_LCS(acrostic, query)) >= 5):
                        already_counted = True
                        break
                if already_counted:
                    break
            if not already_counted:
                print("\t".join(output[k]))"""
        recall[k] = tp/all_tp
    if log:
        for label in true_labels:
            for acrostic, page in label:
                print(f"Did not find {acrostic} in {page}")
    return recall


def main(args):
    fig, ax = plt.subplots(layout='constrained')
    for language, labels, predictions, name in args.data:
       recall = get_recall(predictions, labels, lang=language, log=args.verbose)
       plt.plot(np.arange(len(recall)), recall, label=name, linestyle="--", linewidth=3)

    plt.legend(loc='upper left', fontsize=36)
    ax.set_ylabel('Recall', fontsize=50)
    ax.set_xlabel('# of results', fontsize=50)
    # one dot for each unit
    ax.tick_params(axis='x', labelsize=36)  # Adjust as needed for the x-axis tick labels
    ax.tick_params(axis='y', labelsize=36)  # Adjust as needed for the y-axis tick labels
    fig.set_size_inches(24, 16)
    ax.set_xscale('log')
    plt.savefig(args.name, dpi=600)


def _is_prediction_tuple(tuple):
    if tuple.count(",") != 3:
        raise argparse.ArgumentTypeError(f"{tuple} is not a comma-separated or has less/more than 4 values")
    language, labels, predictions, name = tuple.split(",")
    if language not in Language.all:
        raise argparse.ArgumentTypeError(f"{language} is not a supported language. "
                                         f"Use one of {','.join(Language.all)}")
    is_file(labels)
    is_file(predictions)
    return (language, labels, predictions, name)


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="Plot recall vs # of results for a set of predictions made on the acrostic identification task dataset.")
    p.add_argument("name", type=str,
                   help="The name of the file to which the figure should be saved.")
    p.add_argument("data", nargs="+", type=_is_prediction_tuple,
                   help="Comma separated (language,labels_file,predictions_file,name) tuple")
    p.add_argument('--verbose', action='store_true',
                   help=f"Print some logging information about how recall is calculated.")
    args = p.parse_args(sys.argv[1:])
    main(args)