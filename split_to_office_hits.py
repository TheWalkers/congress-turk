import csv
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description=
        'Generate a CSV for Mech Turk HITs gathering district office data.')
    parser.add_argument("office_lists",
        help="CSV results of MTurk district office list HITs.")
    parser.add_argument("-o", "--out",
        help="destination for CSV file",
        type=argparse.FileType('w'),
        default='-')  # '-' => stdout

    return parser.parse_args()


def convert_row(row):
    offices = row['Answer.district_offices'].strip().split("\n")
    for office in offices:
        yield {'id': row['Input.id'],
               'url': row['Input.url'],
               'name': row['Input.name'],
               'state': row['Input.state'],
               'office': office.strip()}

def split_to_office_hits():
    args = parse_args()

    out_fields = "id url name state office".split()
    writer = csv.DictWriter(args.out, fieldnames=out_fields)
    writer.writeheader()

    for row in csv.DictReader(open(args.office_lists)):
        for row_out in convert_row(row):
            writer.writerow(row_out)


if __name__ == '__main__':
    split_to_office_hits()
