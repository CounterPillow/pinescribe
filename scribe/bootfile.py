from collections import namedtuple
from pprint import pprint
from struct import unpack


class BootfileException(Exception):
    def __init__(self, msg):
        super(BootfileException, self).__init__(msg)


def parse_entry(f, offset, size):
    fields = {
        'size': 'B',
        'type': 'i',
        'name': '40s',       # 20 long wchar
        'pld_offset': 'I',
        'pld_size': 'I',
        'pld_delay': 'I',    # what
    }

    f.seek(offset)

    entry = namedtuple('Entry', ' '.join(fields.keys()))
    e = entry._asdict(entry._make(unpack('<' + ''.join(fields.values()), f.read(size))))

    if e['size'] != size:
        raise BootfileException("Headers disagree about entry sizes, file may be broken?")

    e['name'] = e['name'].decode('utf-16').split('\x00')[0]

    return e


def parse_header(f):
    fields = {
        'tag': '4s',
        'size': 'H',
        'version': 'I',
        'merge_version': 'I',
        'year': 'H',
        'month': 'B',
        'day': 'B',
        'hour': 'B',
        'minute': 'B',
        'second': 'B',
        'support_chip': 'i',
        'entry471_count': 'B',
        'entry471_offset': 'I',
        'entry471_size': 'B',
        'entry472_count': 'B',
        'entry472_offset': 'I',
        'entry472_size': 'B',
        'entryloader_count': 'B',
        'entryloader_offset': 'I',
        'entryloader_size': 'B',
        'sign_flag': 'B',
        'rc4_flag': 'B',
        'RESERVED': '57s'
        # Allegedly, the last 4 bytes of this reserved thing is the CRC. but I
        # have nothing to indicate that this is true since it's always 0.
    }

    header = namedtuple('Header', ' '.join(fields.keys()))
    h = header._asdict(header._make(unpack('<' + ''.join(fields.values()), f.read(102))))
    pprint(h, sort_dicts=False)
    if h['tag'] != b'LDR ':
        raise BootfileException("not a valid loader file")

    entries = {
        '471': [],
        '472': [],
        'loader': [],
    }

    for et in entries:
        count = h[f'entry{et}_count']
        offset = h[f'entry{et}_offset']
        size = h[f'entry{et}_size']

        for i in range(count):
            actual_offset = offset + size * i
            entries[et].append(parse_entry(f, actual_offset, size))

    pprint(entries, sort_dicts=False)
