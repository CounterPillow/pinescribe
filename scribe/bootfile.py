from collections import namedtuple
from struct import unpack
from zlib import crc32


class BootfileException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RKLDREntry:
    __slots__ = ['name', 'pld_offset', 'pld_size', 'pld_delay', 'pld', 'crc']

    def __init__(self, name, pld_offset, pld_size, pld_delay):
        self.name = name
        self.pld_offset = pld_offset
        self.pld_size = pld_size
        self.pld_delay = pld_delay
        self.pld = None

    def __repr__(self):
        status = "read" if self.has_pld() else "unread"
        r = (f"{type(self)}: {self.name} at {self.pld_offset}, "
             f"size {self.pld_size}, delay {self.pld_delay}, {status}")
        return r

    def read_payload(self, f):
        f.seek(self.pld_offset)
        self.pld = f.read(self.pld_size)
        self.crc = crc32(self.pld)

    def has_pld(self):
        return self.pld is not None


class RK471Entry(RKLDREntry):
    def __init__(self, name, pld_offset, pld_size, pld_delay):
        super().__init__(name, pld_offset, pld_size, pld_delay)


class RK472Entry(RKLDREntry):
    def __init__(self, name, pld_offset, pld_size, pld_delay):
        super().__init__(name, pld_offset, pld_size, pld_delay)


class RKLoaderEntry(RKLDREntry):
    def __init__(self, name, pld_offset, pld_size, pld_delay):
        super().__init__(name, pld_offset, pld_size, pld_delay)


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

    t = {0x1: RK471Entry, 0x2: RK472Entry, 0x4: RKLoaderEntry}[e['type']]
    eo = t(e['name'], e['pld_offset'], e['pld_size'], e['pld_delay'])

    return eo


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

    h['entries'] = entries
    return h
