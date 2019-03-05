import re
import smartystreets  # https://github.com/bennylope/smartystreets.py/
import smarty_creds


smarty = smartystreets.Client(
    smarty_creds.SMARTY_AUTH_ID, smarty_creds.SMARTY_AUTH_TOKEN)


HIGH_PRECISION = ('Zip7', 'Zip8', 'Zip9')


memo = {}


def normalize_address(row):
    """
    Normalize and geocode using smartystreets.

    Updates given row in place.
    """
    before = {
        'street': row["Answer.address"].strip(),
        'city': row["Answer.city"].strip(),
        'state': row["Answer.state"].strip(),
        'zipcode': row["Answer.zip"].strip(),
    }
    if not before.get('street') and (
            before.get('zipcode') or
            (before.get('city') and before.get('state'))):
        return

    memo_key = tuple(sorted(before.items()))

    kwargs = {
        'candidates': 1,
        'match': 'range',
        **before
    }

    if memo_key in memo:
        r = memo[memo_key]
    else:
        r = memo[memo_key] = smarty.street_address(kwargs)

    if not r:
        return

    a = r['analysis']
    if 'footnotes' in a:
        if re.match('(C|F)#', a['footnotes']):
            return

    components = r['components']
    metadata = r['metadata']

    after = {
        'Answer.address': r.get('delivery_line_1', ''),
        'Answer.city': components.get('city_name', ''),
        'Answer.state': components.get('state_abbreviation', ''),
    }

    zipcode = components.get('zipcode', '')
    plus4 = components.get('plus4_code')
    if plus4:
        zipcode = '%s-%s' % (zipcode, plus4)

    if zipcode:
        after['Answer.zip'] = zipcode

    if metadata.get('precision') in HIGH_PRECISION:
        after['latitude'] = metadata['latitude']
        after['longitude'] = metadata['longitude']

    row.update(after)
