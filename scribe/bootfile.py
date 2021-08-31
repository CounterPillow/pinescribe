from collections import namedtuple
from struct import unpack


class BootfileException(Exception):
    def __init__(self, msg):
        super(BootfileException, self).__init__(msg)


def parse_header(f):
    fields = {
        'tag':'4s',
        'size':'H',
        'version':'I',
        'merge_version':'I',
        'year':'H',
        'month':'B',
        'day':'B',
        'hour':'B',
        'minute':'B',
        'second':'B',
        'support_chip':'i',
        'entry471_count':'B',
        'entry471_offset':'I',
        'entry471_size':'B',
        'entry472_count':'B',
        'entry472_offset':'I',
        'entry472_size':'B',
        'entryloader_count':'B',
        'entryloader_offset':'I',
        'entryloader_size':'B',
        'sign_flag':'B',
        'rc4_flag':'B',
        'RESERVED':'57s'
        # Allegedly, the last 4 bytes of this reserved thing is the CRC. but I
        # have nothing to indicate that this is true since it's always 0.
    }

    header = namedtuple('Header', ' '.join(fields.keys()))
    h = header._asdict(header._make(unpack('<' + ''.join(fields.values()), f.read(102))))
    print(h)
    if h['tag'] != b'LDR ':
        raise BootfileException("not a valid loader file")
