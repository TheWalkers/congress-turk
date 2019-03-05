import re
from reconcile_turk_results import TurkResultReconciler


def pyaddress_normalize(before):
    if not before:
        return before
    try:
        addr = parser.parse_address(before)
    except (UnicodeDecodeError, address.address.InvalidAddressException), e:
        #print "Error normalizing %s: %s" % (before, e)
        return before
    after = " ".join([f for f in
                      (addr.house_number, addr.street_prefix,
                       addr.street, addr.street_suffix) if f])
    return after

try:
    import address  # https://github.com/SwoopSearch/pyaddress
    parser = address.AddressParser()
    normalize_address = pyaddress_normalize
except ImportError:
    normalize_address = lambda s: s


def remove_empty(s):
    if s == '{}':
        s = ''
    return s


def remove_not_available(s):
    return re.sub(r'^n\s*\/\s*a$', '', s.strip(), flags=re.I)


def normalize_phone(phone):
    return re.sub(r'.*(\d{3}).*(\d{3}).*(\d{4}).*', r'\1-\2-\3', phone)


class DetailTaskResultReconciler(TurkResultReconciler):
    STANDARD_PROCESSORS = [remove_empty, remove_not_available]
    FIELD_PROCESSORS = {
        'phone': [normalize_phone],
        'fax': [normalize_phone],
        'address': [normalize_address],
    }

    def equal(self, a, b):
        return a['Answer.address'] == b['Answer.address']

    def preprocessors(self, field):
        field = field.replace('Answer.', '')
        return self.STANDARD_PROCESSORS + self.FIELD_PROCESSORS.get(field, [])

    def preprocess_row(self, row):
        for field, answer in self.answers(row).items():
            for proc in self.preprocessors(field):
                answer = proc(answer)
            row[field] = answer
        return row


if __name__ == '__main__':
    DetailTaskResultReconciler().reconcile_results()
