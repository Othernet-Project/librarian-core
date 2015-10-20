import random
import string
import urlparse


def generate_random_key(letters=True, digits=True, punctuation=True,
                        length=50):
    charset = []
    if letters:
        charset.append(string.ascii_letters)
    if digits:
        charset.append(string.digits)
    if punctuation:
        charset.append(string.punctuation)

    if not charset:
        return ''

    chars = (''.join(charset).replace('\'', '')
                             .replace('"', '')
                             .replace('\\', ''))
    return ''.join([random.choice(chars) for i in range(length)])


def from_csv(raw_value):
    return [val.strip() for val in (raw_value or '').split(',') if val]


def to_csv(values):
    return ','.join(values)


def row_to_dict(row):
    return dict((key, row[key]) for key in row.keys()) if row else {}
