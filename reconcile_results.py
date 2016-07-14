import argparse
import csv
import re
import string
from difflib import unified_diff
from itertools import groupby
from subprocess import call

def parse_args():
    parser = argparse.ArgumentParser(description=
        'Diff and merge results of a List Offices task')
    parser.add_argument("office_lists",
        help="CSV results of MTurk district office list HITs.",
        type=argparse.FileType('r'),
        default='-')
    parser.add_argument("-o", "--out",
        help="destination for CSV file",
        type=argparse.FileType('wb', 0), 
        default='-')  # '-' => stdout

    return parser.parse_args()


def normalize_row(row):
    offices = [o.strip()
               for o in row['Answer.district_offices'].strip().split('\n')]
    dc = re.compile('washington,? d\.?c\.?', re.I)
    offices = [o for o in offices if not dc.match(o)]
    offices.sort(key=string.lower)
    row['Answer.district_offices'] = offices
    return row
 

def combine_rows(rows, key_column='HITId'):
    key = lambda r: r.get(key_column)
    rows.sort(key=key)
    return groupby(rows, key=key)

def reconcile_group(group):
    group = list(group)
    first = group[0]
    if len(group) == 1:
        return first
    assert len(group) == 2, "Can only reconcile 1 or 2 answers"
    lowered = [[o.lower() for o in row['Answer.district_offices']]
               for row in group]
    if lowered[0] == lowered[1]:
        return first
   
    print "Discrepancy for %s (%s):" % (group[0]['Input.name'], group[0]['Input.url'])
    for ln in unified_diff(lowered[0], lowered[1], fromfile="entry 1", tofile="entry 2"):
        print ln

    while True:
        answer = raw_input("Fix (1/2/m/o/?): ")
        if answer.isdigit():
            return group[int(answer) - 1]
        elif answer == 'm':
            offices = sorted(list(set(lowered[0] + lowered[1])))
            first['Answer.district_offices'] = offices
            return first
        elif answer == 'o':
            call(["open", first['Input.url']])
        elif answer == '?':
            print (" 1 -- choose first '-' option\n"
                   " 2 -- choose second '+' option\n"
                   " m -- merge lists\n"
                   " o -- open URL in browser\n"
                   " ? -- this help text\n")
        else:
            raise Exception("Unknown answer %s" % answer)

def split_row(row):
    offices = row['Answer.district_offices']
    for office in offices:
        yield {'id': row['Input.id'],
               'url': row['Input.url'],
               'state': row['Input.state'],
               'name': row['Input.name'],
               'office': office.strip()}


def reconcile_results():
    args = parse_args()
    out_fields = "id url name state office".split()
    reader = csv.DictReader(args.office_lists)
    writer = csv.DictWriter(args.out, fieldnames=out_fields)
    writer.writeheader()
    rows = [normalize_row(row) for row in reader]
    grouped_rows = combine_rows(rows)
    for _, group in grouped_rows:
        for row in split_row(reconcile_group(group)):
            writer.writerow(row)

if __name__ == '__main__':
    reconcile_results()

