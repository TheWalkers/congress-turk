import re
from reconcile_turk_results import TurkResultReconciler

try:
    from smarty_normalize import normalize_address

except ImportError:
    print("smarty not found, not doing address normalization")
    normalize_address = None


def remove_empty(s):
    if s == '{}':
        s = ''
    return s


def remove_not_available(s):
    if not s:
        return s
    return re.sub(r'^n\s*\/\s*a$', '', s.strip(), flags=re.I)


def normalize_phone(phone):
    return re.sub(r'.*(\d{3}).*(\d{3}).*(\d{4}).*', r'\1-\2-\3', phone)


class DetailTaskResultReconciler(TurkResultReconciler):
    STANDARD_PROCESSORS = [remove_empty, remove_not_available]
    FIELD_PROCESSORS = {
        'phone': [normalize_phone],
        'fax': [normalize_phone],
    }

    @property
    def output_fields(self):
        fieldnames = self.reader.fieldnames
        if normalize_address:
            fieldnames += ['latitude', 'longitude']
        return fieldnames

    def tempfile_edit(self, row):
        def addr(row):
            return [row.get('Answer.' + f) for f in
                    ['address', 'city', 'state', 'zip']]

        orig_addr = addr(row)

        super(DetailTaskResultReconciler, self).tempfile_edit(row)

        # if address fields changed, normalize again
        if normalize_address and addr(row) != orig_addr:
            normalize_address(row)
        return row

    def preprocessors(self, field):
        field = field.replace('Answer.', '')
        return self.STANDARD_PROCESSORS + self.FIELD_PROCESSORS.get(field, [])

    def preprocess_row(self, row):
        for field, answer in self.answers(row).items():
            for proc in self.preprocessors(field):
                answer = proc(answer)
            row[field] = answer

        if normalize_address:  # operates on whole row, handle separately
            try:
                normalize_address(row)
            except Exception as e:
                print("Error normalizing %r: %s" % (row, e))

        return row


if __name__ == '__main__':
    DetailTaskResultReconciler().reconcile_results()
