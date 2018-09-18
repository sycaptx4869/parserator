#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from builtins import zip
from builtins import str
from builtins import range
from lxml import etree
import sys
import os.path
from . import data_prep_utils
import re
import csv
from argparse import ArgumentParser
from collections import OrderedDict
import io
import subprocess
if sys.version < '3' :
    from backports import csv
else :
    import csv

def consoleLabel(raw_strings, labels, module):
    print('\nStart console labeling!\n')
    valid_input_tags = OrderedDict([(str(i), label) for i, label in enumerate(labels)])
    printHelp(valid_input_tags)

    valid_responses = ['y', 'n', 's', 'f', '']
    finished = False

    strings_left_to_tag = raw_strings.copy()
    total_strings = len(raw_strings)
    tagged_strings = set([])

    for i, raw_sequence in enumerate(raw_strings, 1):

        if not finished:

            print('\n(%s of %s)' % (i, total_strings))
            print('-'*50)
            print('STRING: %s' %raw_sequence)

            preds = module.parse(raw_sequence)

            user_input = None
            while user_input not in valid_responses :

                friendly_repr = [(token[0].strip(), token[1]) for token in preds]
                print_table(friendly_repr)

                sys.stderr.write('Is this correct? (y)es / (n)o / (s)kip / (f)inish tagging / (h)elp\n')
                user_input = sys.stdin.readline().strip()

                if user_input =='y':
                    tagged_strings.add(tuple(preds))
                    strings_left_to_tag.remove(raw_sequence)

                elif user_input =='n':
                    corrected_string = manualTagging(preds,
                                                valid_input_tags)
                    tagged_strings.add(tuple(corrected_string))
                    strings_left_to_tag.remove(raw_sequence)

                elif user_input in ('h', 'help', '?')  :
                    printHelp(valid_input_tags)

                elif user_input in ('' or 's') :
                    print('Skipped\n')
                elif user_input == 'f':
                    finished = True

    print('Done! Yay!')
    return tagged_strings, strings_left_to_tag

def check_dup(raw_sequence):
    seen = set()
    for item in raw_sequence:
        if item[0] not in seen:
            seen.add(item[0])
        else:
            return True
    return False



def batch_consoleLabel(raw_strings, labels, module):
    print('\nStart batch console labeling!\n')
    valid_input_tags = OrderedDict([(str(i), label) for i, label in enumerate(labels)])
    printHelp(valid_input_tags)

    valid_responses = ['y', 'n', 'h']

    raw_strings = list(raw_strings)
    total_strings = len(raw_strings)
    initial_tagged_strings = []
    tagged_strings = []
    strings_left_to_tag = []

    for raw_sequence in raw_strings:
        preds = module.parse(raw_sequence)
        if not check_dup(preds):
            initial_tagged_strings.append(tuple(preds))
        else:
            strings_left_to_tag.append(raw_sequence)



    with open('labeled_training_data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["RawAddress"]+labels)
        i = 0
        for address in initial_tagged_strings:
            address_list = [raw_strings[i]]
            i += 1
            for label in labels:
                label_string = ""
                for couple in address:
                    if couple[1] == label and label_string == "":
                        label_string += couple[0]
                    elif couple[1] == label:
                        label_string += " "
                        label_string += couple[0]
                    else:
                        continue
                address_list.append(label_string)
            writer.writerow(address_list)


    # p = subprocess.Popen('open -W labeled_training_data.csv', shell=True)
    # p.wait()

    input("Press any key to continue...")

    with open('labeled_training_data.csv', newline='') as csvfile:
        tagged_strings = []
        reader = csv.reader(csvfile)
        tagged_string = []
        header = next(reader)[1:]
        line = 0
        for row in reader:
            row = row[1:]
            processed_row = []
            for i in range(len(row)):
                addr = row[i]
                tag = header[i]
                if addr:
                    for a in addr.split(' '):
                        pair = (a,tag)
                        processed_row.append(pair)

            original_row = [oa for oa, t in initial_tagged_strings[line]]
            processed_row.sort(key = lambda at: original_row.index(at[0]))

            if processed_row:
                processed_row = tuple(processed_row)
                tagged_strings.append(processed_row)
            line += 1

    return tagged_strings, strings_left_to_tag


def print_table(table):
    col_width = [max(len(x) for x in col) for col in zip(*table)]
    for line in table:
        print(u"| %s |" % " | ".join(u"{:{}}".format(x, col_width[i])
                                     for i, x in enumerate(line)))


def manualTagging(preds, valid_input_tags):
    tagged_sequence = []
    for token, predicted_tag in preds:
        while True:
            print('What is \'%s\' ? If %s hit return' % (token, predicted_tag))
            user_choice = sys.stdin.readline().strip()
            if user_choice == '' :
                tag = predicted_tag
                break
            elif user_choice in valid_input_tags :
                tag = valid_input_tags[user_choice]
                break
            elif user_choice in ('h', 'help', '?') :
                printHelp(valid_input_tags)
            elif user_choice == 'oops':
                print('No worries! Let\'s start over in labeling this string')
                tagged_sequence_redo = manualTagging(preds, valid_input_tags)
                return tagged_sequence_redo
            else:
                print("That is not a valid tag. Type 'help' to see the valid inputs")

        tagged_sequence.append((token, tag))
    return tagged_sequence


def naiveConsoleLabel(raw_strings, labels, module):

    print('\nStart console labeling!\n')
    valid_input_tags = OrderedDict([(str(i), label) for i, label in enumerate(labels)])
    printHelp(valid_input_tags)

    valid_responses = ['t', 's', 'f', '']
    finished = False

    strings_left_to_tag = raw_strings.copy()
    total_strings = len(raw_strings)
    tagged_strings = set([])

    for i, raw_sequence in enumerate(raw_strings, 1):
        if not finished:

            print('\n(%s of %s)' % (i, total_strings))
            print('-'*50)
            print('STRING: %s' %raw_sequence)

            tokens = module.tokenize(raw_sequence)

            user_input = None
            while user_input not in valid_responses :

                sys.stderr.write('(t)ag / (s)kip / (f)inish tagging / (h)elp\n')
                user_input = sys.stdin.readline().strip()

                if user_input =='t' or user_input == '':
                    tagged_sequence = naiveManualTag(tokens, valid_input_tags)
                    tagged_strings.add(tuple(tagged_sequence))
                    strings_left_to_tag.remove(raw_sequence)
                elif user_input in ('h', 'help', '?') :
                    printHelp(valid_input_tags)
                elif user_input == 's':
                    print('Skipped\n')
                elif user_input == 'f':
                    finished = True

    print('Done! Yay!')
    return tagged_strings, strings_left_to_tag

def naiveManualTag(raw_sequence, valid_input_tags):
    sequence_labels = []
    for token in raw_sequence:
        valid_tag = False
        while not valid_tag:
            print('What is \'%s\' ?' %token)
            user_input_tag = sys.stdin.readline().strip()
            if user_input_tag in valid_input_tags:
                valid_tag = True
            elif user_input_tag in ('h', 'help', '?') :
                printHelp(valid_input_tags)
            elif user_input_tag == 'oops':
                print('No worries! Let\'s start over in labeling this string')
                sequence_labels_redo = naiveManualTag(raw_sequence, valid_input_tags)
                return sequence_labels_redo
            else:
                print("That is not a valid tag. Type 'help' to see the valid inputs")

        token_label = valid_input_tags[user_input_tag]
        sequence_labels.append((token, token_label))
    return sequence_labels

def printHelp(valid_input_tags):
    print('*'*50)
    print('These are the tags available for labeling:')
    for valid_input in valid_input_tags:
        print('%s : %s' %(valid_input, valid_input_tags[valid_input]))
    print("\ntype 'help' at any time to see labels")
    print("type 'oops' if you make a labeling error\n")
    print('*'*50, '\n')

def label(module, infile, outfile, xml, batch = False):

    training_data = data_prep_utils.TrainingData(xml, module)

    reader = csv.reader(infile)
    strings = set(row[0] for row in reader)

    labels = module.LABELS

    if module.TAGGER:
        if not batch:
            labeled_list, raw_strings_left = consoleLabel(strings, labels, module)
        else:
            labeled_list, raw_strings_left = batch_consoleLabel(strings, labels, module)
    else:
        labeled_list, raw_strings_left = naiveConsoleLabel(strings, labels, module)

    training_data.extend(labeled_list)

    with open(outfile, 'wb'):
        training_data.write(outfile)

    file_slug = os.path.basename(infile.name)
    if not file_slug.startswith('unlabeled_'):
        file_slug = 'unlabeled_' + file_slug
    remainder_file = os.path.dirname(infile.name) + file_slug

    data_prep_utils.list2file(raw_strings_left, remainder_file)
