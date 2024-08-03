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


def get_acrostic_groups(filename, lang, prohibited_labels):
    results = [line.strip("\n").split("\t") for line in open(filename).readlines()[1:]]
    groups = []
    join_with_previous = False  # cluster acrostics that are split into multiple files together to count them as one
    for labels, acrostic, page in results:
        does_not_count_during_evaluation = False
        for label in prohibited_labels:
            if label in labels:
                does_not_count_during_evaluation = True
                break
        if does_not_count_during_evaluation:
            join_with_previous = join_with_previous and 's' in labels
            continue
        acrostic = re.sub(" ", "", format(acrostic, lang))
        if not join_with_previous:
            groups.append([(labels, acrostic,page)])
        else:
            groups[-1].append((labels, acrostic,page))
        join_with_previous = 's' in labels
    groups = [tuple(x) for x in groups]
    return groups


def get_groups_that_count_towards_recall(filename, lang):
    return get_acrostic_groups(filename, lang, 'no23468itwe')

def get_groups_that_count_towards_precision(filename, lang):
    return get_acrostic_groups(filename, lang, 'o23468we')


def get_precision_recall_f1(filename, truth_file, lang, log=False):
    groups = get_groups_that_count_towards_precision(truth_file, lang)
    groups_not_covered = get_groups_that_count_towards_recall(truth_file, lang)
    groups_to_cover = len(groups_not_covered)
    output = open(filename).readlines()[1:]
    output = [line.strip("\n").split("\t") for line in output]
    output.reverse()
    recall = np.zeros(len(output))
    precision = np.zeros(len(output))
    f1 = np.zeros(len(output))
    false_positives = 0
    for k in range(len(output)):
        title, candidate, _, _, _, cluster, _, _, prefix, postfix, _ = output[k]
        query_full = prefix + cluster + postfix
        query = re.sub(' ', '', format(query_full, lang))
        to_remove = []
        for group in groups_not_covered:
            for labels, acrostic, page in group:
                if title == page and (acrostic in query or len(find_LCS(acrostic, query)) >= 5):
                    if group not in to_remove:
                        to_remove.append(group)
        if len(to_remove) == 0:
            is_a_true_positive = False
            for group in groups:
                for labels, acrostic, page in group:
                    if title == page and (acrostic in query or len(find_LCS(acrostic, query)) >= 5):
                        is_a_true_positive = True
                        break
                if is_a_true_positive:
                    break
            if not is_a_true_positive:
                false_positives += 1
        recall[k] = (groups_to_cover - len(groups_not_covered) + len(to_remove)) / groups_to_cover
        precision[k] = (k + 1 - false_positives) / (k + 1)
        f1[k] = 0 if recall[k] == 0 and precision[k] == 0 else 2 * precision[k] * recall[k] / (precision[k] + recall[k])
        for group in to_remove:
            if log:
                print(f"Hit {group[0][1]}, k={k}, recall={recall[k]}, precision={precision[k]}, f1={f1[k]}")
            groups_not_covered.remove(group)
    if log:
        for group in groups_not_covered:
            for labels, acrostic, page in group:
                print(f"Did not find {acrostic} in {page}")
    if log:
        print(f"Max recall: {max(recall)}, max precision: {max(precision)}, max f1: {max(f1)}")
    return precision, recall, f1


def main(args):
    fig, ax = plt.subplots(layout='constrained')
    line_styles = ['dotted', 'dashed', 'dashdot', ((0, (1, 10))), (0, (5, 10)), (0, (5, 1)), (0, (3, 5, 1, 5, 1, 5))]
    for i, (language, labels, predictions, name) in enumerate(args.data):
       precision, recall, f1 = get_precision_recall_f1(predictions, labels, lang=language, log=args.verbose)
       to_plot = recall if args.metric == "recall" else precision if args.metric == "precision" else f1
       plt.plot(np.arange(len(to_plot)), to_plot, label=name, linestyle=line_styles[i % len(line_styles)], linewidth=3)

    if args.metric == "precision":
        plt.legend(loc='upper right', fontsize=36)
    else:
        plt.legend(loc='upper left', fontsize=36)
    ax.set_ylabel(args.metric[0].upper() + args.metric[1:], fontsize=50)
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
    p.add_argument('metric', choices=['precision', 'recall', "f1"], help="Metric to plot")
    p.add_argument("name", type=str,
                   help="The name of the file to which the figure should be saved.")
    p.add_argument("data", nargs="+", type=_is_prediction_tuple,
                   help="Comma separated (language,labels_file,predictions_file,name) tuple")
    p.add_argument('--verbose', action='store_true',
                   help=f"Print some logging information about how recall is calculated.")
    args = p.parse_args(sys.argv[1:])
    main(args)