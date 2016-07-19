import argparse
import csv
import re
import os
import string
import tempfile
import yaml
from collections import OrderedDict
from difflib import unified_diff
from itertools import groupby
from subprocess import call, check_call

from termcolor import colored

EDITOR = os.environ.get('EDITOR', 'vim')



class TurkResultReconciler(object):

    def __init__(self):
        args = self.parse_args()

        self.reader = csv.DictReader(args.source)
        self.rows = None

        self.writer = csv.DictWriter(args.destination,
                                     fieldnames=self.output_fields)
        if not args.destination.tell():
            self.writer.writeheader()

        self.review = csv.DictWriter(args.review,
                                     fieldnames=self.output_fields)

        rows = [self.preprocess_row(r) for r in self.reader]

        if args.review.tell():
            args.review.seek(0)
            reviewed = set([self.row_key(r)
                            for r in csv.DictReader(args.review)])
            rows = [r for r in rows if self.row_key(r) not in reviewed]
        else:
            self.review.writeheader()

        self.rows = rows

    def row_key(self, row):
        return row['AssignmentId']

    def parse_args(self):
        parser = argparse.ArgumentParser(description=
            'Diff and merge results of a Mechanical Turk task')
        parser.add_argument("source",
            help="CSV results of MTurk HITs.",
            type=argparse.FileType('r'))
        parser.add_argument("destination",
            help="destination for CSV file of reconciled results",
            type=argparse.FileType('a+', 0))
        parser.add_argument("review",
            help="Reviewed CSV file to re-upload to Mechanical Turk",
            type=argparse.FileType('a+', 0))

        return parser.parse_args()

    @property
    def output_fields(self):
        return self.reader.fieldnames

    def combine_by_hit(self, key_column='HITId'):
        key = lambda r: r.get(key_column)
        rows = sorted(self.rows, key=key)
        return groupby(rows, key=key)

    def preprocess_row(self, row):
        # subclasses may change this
        return row

    def postprocess_row(self, row):
        # subclasses may change this
        return row

    def answers(self, row):
        return {f: row[f] for f in row.keys() if f.startswith('Answer.')}

    def inputs(self, row):
        return {f: row[f] for f in row.keys() if f.startswith('Input.')}
        
    def format_for_diff(self, row):
        return yaml.dump(self.answers(row), default_flow_style=False)

    def tempfile_edit(self, row):
        # from http://stackoverflow.com/a/6309753/174653
        initial_message = self.format_for_diff(row)
        with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
            tf.write(initial_message)
            tf.flush()
            check_call([EDITOR, tf.name])
           
            with open(tf.name) as f:
                row.update(yaml.load(f))

    def print_diff(self, row1, row2):
        print "Discrepancy for {HITId}".format(**row1)
        print yaml.dump(self.inputs(row1), default_flow_style=False)

        formatted = [self.format_for_diff(r).split('\n') for r in [row1, row2]]
        diff = unified_diff(*formatted, n=20)

        for s in diff:
            if s.strip() in ('---', '+++'):
                continue
            
            if s.startswith('-'):
                print colored("{:<40}".format(s[1:]), 'red')
            elif s.startswith('+'):
                print colored("{:<40}".format(s[1:]), 'blue')
            elif s.startswith(' '):
                print s[1:]
                #print "{:<40} {:<40}".format(s[1:], s[1:])

    def equal(self, *rows):
        formatted = [self.format_for_diff(row).lower() for row in rows]
        return len(set(formatted)) == 1

    def prompt_reconcile(self, row1, row2):
        while True:
            self.print_diff(row1, row2)
            answer = raw_input("Fix (1/2/e1/e2/R1/R2/o/?): ")
            if answer.isdigit():
                return {'1': row1, '2': row2}[answer]
            elif answer == 'o':
                call(["open", row1['Input.url']])
            elif answer.startswith('e'):
                edit = {'1': row1, '2': row2}[answer[1]]
                self.tempfile_edit(edit)
                print edit
            elif answer.startswith('R'):
                reason = raw_input("Reason this entry is rejected: ")
                rejected = {'1': row1, '2': row2}[answer[1]]
                rejected['Approve'] = ''
                rejected['Reject'] = reason
            elif answer == '?':
                print """
                    1  -- choose left option
                    2  -- choose right '+' option
                    e1 -- edit left option
                    e2 -- edit right option
                    R1 -- REJECT left option
                    R2 -- REJECT right option
                    o  -- open URL in browser
                    ?  -- this help text
                """
            else:
                print "Oops! Unsupported option {}".format(answer)

    def reconcile_group(self, group):
        """
        For a group of HIT results, let the user reconcile any differences.
        """
        group = tuple(group)
        assert len(group) == 2, "Only works on pairs"

        row1, row2 = group
        row1['Approve'] = 'x'
        row2['Approve'] = 'x'
        result = None

        if self.equal(row1, row2):
            result = row1
        else:
            result = self.prompt_reconcile(row1, row2)

        result = self.postprocess_row(result)
        self.writer.writerow(result)

        self.review.writerow(row1)
        self.review.writerow(row2)

    def reconcile_results(self):
        for _, group in self.combine_by_hit():
            self.reconcile_group(group)


if __name__ == '__main__':
    TurkResultReconciler().reconcile_results()



