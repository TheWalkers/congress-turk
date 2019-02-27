import argparse
import csv
import yaml
from decimal import Decimal


def load_data(source_file):
    return yaml.load(open(source_file))


def get_predicates(args):
    predicates = []  # a list of tests for each legislator record

    if args.all:
        predicates.append(lambda r: True)
        return predicates

    if args.names: 
        names = [n.lower() for n in args.names]
        predicates.append(lambda r: r['name']['last'].lower() in names)

    if args.type:
        predicates.append(lambda r: r['terms'][-1]['type'] == args.type)

    if args.districts:
        districts = set(args.districts)
        def is_district(record):
            term = record['terms'][-1]  # last term is current term
            if term['type'] != 'rep':
                return False
            district = "{}_{}".format(term['state'],
                                      str(term['district']).zfill(2))
            return district in districts

        predicates.append(is_district)

    if args.seats:
        seats = set(args.seats)
        def is_seat(record):
            term = record['terms'][-1]  # last term is current term
            if term['type'] != 'sen':
                return False
            rank_num = {'senior': 1, 'junior': 2}[term['state_rank']]
            seat_code = "{state}_{rank_num}".format(rank_num=rank_num, **term)
            return seat_code in seats

        predicates.append(is_seat)

    return predicates


def get_legislators(data, predicates):
    for record in data:
        if any((p(record) for p in predicates)):
            yield record

    
def generate_header():
    return "id name state url".split()


def generate_row(record):
    id = record['id']['bioguide']
    name = record['name']
    name = name.get('official_name', ' '.join([name['first'], name['last']]))
    term = record['terms'][-1]  # current term
    hon = 'Sen.' if term['type'] == 'sen' else 'Rep.'
    name = ' '.join([hon, name])
    state = term['state']
    url = term.get('url')
    return [id, name, state, url]


def generate_csv(legislators, outfile):
    writer = csv.writer(outfile)
    writer.writerow(generate_header())
    for legislator in legislators:
        row = generate_row(legislator)
        if not row[2]:  # check that URL is not empty
            continue
        writer.writerow(row)


def get_args():
    parser = argparse.ArgumentParser(description=
        'Generate a CSV for Mech Turk HITs gathering district office data.')
    parser.add_argument("source_file",
        help="source for legislator data (e.g., legislators-current.yaml)")
    parser.add_argument("-o", "--out",
        help="destination for CSV file",
        type=argparse.FileType('w'),
        default='-')  # '-' => stdout

    legislators = parser.add_argument_group('Choose legislators')
    legislators.add_argument("-a", "--all", action="store_true")
    legislators.add_argument("-t", "--type", action="store", help="Chamber type ('rep' or 'sen')")
    legislators.add_argument("--names", nargs="*", help="Last names of legislators (may match multiple)")
    legislators.add_argument("--seats", nargs="*",
        help="Seats of Senator, e.g. WA_1 or WA_2")
    legislators.add_argument("--districts", nargs="*",
        help="Districts of House Representatives, e.g. CA_01")

    args = parser.parse_args()

    if not any([args.all, args.type, args.names, args.seats, args.districts]):
        parser.error("Need at least one of --all, --names, --seats, --districts.")

    return args 

def generate_hits(args):
    source_data = load_data(args.source_file)
    predicates = get_predicates(args)
    legislators = get_legislators(source_data, predicates)
    generate_csv(legislators, args.out)


if __name__ == "__main__":
    args = get_args()
    generate_hits(args)



