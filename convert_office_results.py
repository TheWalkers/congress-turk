import argparse
import csv
import re
import rtyaml as yaml
from collections import defaultdict, OrderedDict
from itertools import groupby, count
from operator import itemgetter

parser = argparse.ArgumentParser(
    description='Convert results of a "details" task to yaml')

parser.add_argument(
    "source",
    help="Reconciled CSV results of MTurk HITs.",
    type=argparse.FileType('r'),
    default='-')

parser.add_argument(
    "ids_source",
    help=("Source from which to get other ids (govtrack, thomas)"
          "(legistators-current.yaml"),
    type=argparse.FileType('r'))

parser.add_argument(
    "destination",
    help="destination for results (legislators-district-offices.yaml)",
    type=argparse.FileType('w'),
    default='-')

args = parser.parse_args()

by_id = itemgetter('Input.id')

rows = list(csv.DictReader(args.source))

rows.sort(key=by_id)
grouped = groupby(rows, key=by_id)

FIELD_ORDER = """
    id
    address suite building
    city state zip
    latitude longitude
    phone fax hours
""".split()


def reorder_office(office):
    return OrderedDict([
        (k, office.get(k))
        for k in FIELD_ORDER
        if office.get(k)])


office_ids = defaultdict(count)


def id_office(bioguide_id, office):

    locality = office.get('city', 'no_city').lower()
    locality = re.sub(r'\W', '_', locality)

    office_id = '-'.join([bioguide_id, locality])

    city_count = next(office_ids[office_id])
    if city_count:
        office_id = '-'.join([office_id, str(city_count)])

    office['id'] = office_id


other_ids = None

# if ids_sources was supplied, build a dict of other ids by bioguide id
if args.ids_source:
    legislators = yaml.load(args.ids_source.read())
    id_types = ['bioguide', 'thomas', 'govtrack']
    other_ids = {el['id']['bioguide']:
                 {t: el['id'][t] for t in id_types if el['id'].get(t)}
                 for el in legislators}

data = []
for key, group in grouped:
    offices = []
    for item in group:
        office = {k.replace("Answer.", ""): v
                  for k, v in item.items()
                  if k.startswith("Answer.") and v.strip()}

        if not (office.get('city') and office.get('state') and
                (office.get('phone') or office.get('address'))):
            print("Missing minimum fields for office: %r" % office)
            continue

        id_office(key, office)

        if 'latitude' in item:
            office['latitude'] = float(item['latitude'])
        if 'longitude' in item:
            office['longitude'] = float(item['longitude'])

        if office.get('suite') and re.match(r'^\d+$', office['suite']):
            office['suite'] = 'Suite ' + office['suite']

        office = reorder_office(office)
        offices.append(office)

    offices.sort(key=lambda o: o.get('city'))

    ids = {'bioguide': key}
    if other_ids:
        ids = other_ids[key]
    data.append({'id': ids, 'offices': offices})

out = yaml.dump(data)
args.destination.write(out)
