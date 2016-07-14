import argparse
import csv
import re
import string
import yaml
from difflib import unified_diff
from itertools import groupby
from subprocess import call

def parse_args():
    parser = argparse.ArgumentParser(description=
        'Diff and merge results of Office Details tasks')
    parser.add_argument("detail_results",
        help="CSV results of MTurk district office detail HITs.",
        type=argparse.FileType('r'),
        default='-')
    parser.add_argument("-o", "--out",
        help="destination for CSV file",
        type=argparse.FileType('wb', 0), 
        default='-')  # '-' => stdout

    return parser.parse_args()


def normalize_phone(phone):
    return re.sub(r'.*(\d{3}).*(\d{3}).*(\d{4}).*', r'\1-\2-\3', phone)


def normalize_row(row):
    for field, value in row.items():
        if field.startswith('Answer.') and value == '{}':
            row[field] = ''
    for field in ['phone', 'fax']:
        fieldname = 'Answer.%s' % field
        row[fieldname] = normalize_phone(row[fieldname])
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

    fields = ["Answer." + k for k in 
              ["address","address2","city","fax","hours","phone","state","zip"]]
    
    answers = [["%s: %s" % (k, a.get(k)) for k in fields] for a in group]

    if answers[0] == answers[1]:
        return first

    print "Discrepancy for %s - %s (%s):" % (first['Input.name'], first['Input.office'], first['Input.url'])
    for ln in unified_diff(answers[0], answers[1], fromfile="entry 1", tofile="entry 2"):
        print ln

    while True:
        fix = raw_input("Fix (1/2/m/o/?): ")
        if fix.isdigit():
            return group[int(fix) - 1]
        # elif fix == 'm':
        #     offices = sorted(list(set(lowered[0] + lowered[1])))
        #     first['Answer.district_offices'] = offices
        #     return first
        elif fix == 'o':
            call(["open", first['Input.url']])
        elif fix == '?':
            print (" 1 -- choose first '-' option\n"
                   " 2 -- choose second '+' option\n"
                   # " m -- merge lists\n"
                   " o -- open URL in browser\n"
                   " ? -- this help text\n")
        else:
            raise Exception("Unknown answer %s" % fix)

def convert_row(row):
    answers = {k.replace('Answer.', ''): v
               for k, v in row.items()
               if k.startswith('Answer.')}
    answers['bioguide'] = row['Input.id']
    return answers

def group_offices(rows):
    key = lambda r: r.get('bioguide')
    rows.sort(key=key)
    grouped = groupby(rows, key=key)
    for k, offices in grouped:
        offices = list(offices)
        for office in offices:
            del office['bioguide']
        yield {'bioguide': k, 'offices': offices}


def reconcile_results():
    args = parse_args()
    out_fields = "id url name state office".split()
    reader = csv.DictReader(args.detail_results)
    rows = [normalize_row(row) for row in reader]
    grouped_rows = combine_rows(rows)
    out = []
    for _, group in grouped_rows:
        reconciled = reconcile_group(group) 
        converted = convert_row(reconciled)
        out.append(converted)
    out = list(group_offices(out))
    yaml.dump(out, args.out, default_flow_style=False)

if __name__ == '__main__':
    reconcile_results()

