import struct
from random import randint


class CBWException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


USB_OPERATION_CODES = {
    0x00: 'TEST_UNIT_READY',
    0x01: 'READ_FLASH_ID',
    0x03: 'TEST_BAD_BLOCK',
    0x04: 'READ_SECTOR',
    0x05: 'WRITE_SECTOR',
    0x06: 'ERASE_NORMAL',
    0x0B: 'ERASE_FORCE',
    0x14: 'READ_LBA',
    0x15: 'WRITE_LBA',
    0x16: 'ERASE_SYSTEMDISK',
    0x17: 'READ_SDRAM',
    0x18: 'WRITE_SDRAM',
    0x19: 'EXECUTE_SDRAM',
    0x1A: 'READ_FLASH_INFO',
    0x1B: 'READ_CHIP_INFO',
    0x1E: 'SET_RESET_FLAG',
    0x1F: 'WRITE_EFUSE',
    0x20: 'READ_EFUSE',
    0x21: 'READ_SPI_FLASH',
    0x22: 'WRITE_SPI_FLASH',
    0x23: 'WRITE_NEW_EFUSE',
    0x24: 'READ_NEW_EFUSE',
    0x25: 'ERASE_LBA',
    0xAA: 'READ_CAPABILITY',
    0xFF: 'DEVICE_RESET',
}


USB_OPERATION_CODE_VALUES = {v: k for k, v in USB_OPERATION_CODES.items()}


USB_DIR_IN = 0x80


USB_DIR_OUT = 0x00


USB_OPCODE_DIR = {
    'TEST_UNIT_READY': USB_DIR_IN,
    'READ_FLASH_ID': USB_DIR_IN,
    'READ_FLASH_INFO': USB_DIR_IN,
    'READ_CHIP_INFO': USB_DIR_IN,
    'READ_EFUSE': USB_DIR_IN,
    'READ_CAPABILITY': USB_DIR_IN,
    'DEVICE_RESET': USB_DIR_OUT,
    'ERASE_SYSTEMDISK': USB_DIR_OUT,
    'SET_RESET_FLAG': USB_DIR_OUT,
    'TEST_BAD_BLOCK': USB_DIR_IN,
    'READ_SECTOR': USB_DIR_IN,
    'READ_LBA': USB_DIR_IN,
    'READ_SDRAM': USB_DIR_IN,
    'READ_SPI_FLASH': USB_DIR_IN,
    'READ_NEW_EFUSE': USB_DIR_IN,
    'WRITE_SECTOR': USB_DIR_OUT,
    'WRITE_LBA': USB_DIR_OUT,
    'WRITE_SDRAM': USB_DIR_OUT,
    'EXECUTE_SDRAM': USB_DIR_OUT,
    'ERASE_NORMAL': USB_DIR_OUT,
    'ERASE_FORCE': USB_DIR_OUT,
    'WRITE_EFUSE': USB_DIR_OUT,
    'WRITE_SPI_FLASH': USB_DIR_OUT,
    'WRITE_NEW_EFUSE': USB_DIR_OUT,
    'ERASE_LBA': USB_DIR_OUT,
}


USB_OPCODE_CBLEN = {
    'TEST_UNIT_READY': 0x06,
    'READ_FLASH_ID': 0x06,
    'READ_FLASH_INFO': 0x06,
    'READ_CHIP_INFO': 0x06,
    'READ_EFUSE': 0x06,
    'READ_CAPABILITY': 0x06,
    'DEVICE_RESET': 0x06,
    'ERASE_SYSTEMDISK': 0x06,
    'SET_RESET_FLAG': 0x06,
    'TEST_BAD_BLOCK': 0x0a,
    'READ_SECTOR': 0x0a,
    'READ_LBA': 0x0a,
    'READ_SDRAM': 0x0a,
    'READ_SPI_FLASH': 0x0a,
    'READ_NEW_EFUSE': 0x0a,
    'WRITE_SECTOR': 0x0a,
    'WRITE_LBA': 0x0a,
    'WRITE_SDRAM': 0x0a,
    'EXECUTE_SDRAM': 0x0a,
    'ERASE_NORMAL': 0x0a,
    'ERASE_FORCE': 0x0a,
    'WRITE_EFUSE': 0x0a,
    'WRITE_SPI_FLASH': 0x0a,
    'WRITE_NEW_EFUSE': 0x0a,
    'ERASE_LBA': 0x0a,
}


CBW_SIGNATURE = 0x43425355


class RKCBWCB:
    __slots__ = ['opcode', 'addr', 'length']

    def __init__(self, opcode: int, length: int):
        if opcode not in USB_OPERATION_CODES.keys():
            raise CBWException(f"{opcode:x} is not a valid opcode")
        self.opcode = opcode
        if length >= 2**16:
            raise CBWException(f"Length {length} is too large (max {2**16 - 1})")
        self.length = length
        self.addr = 0

    def to_bytes(self) -> bytes:
        return struct.pack('<BBIBH7s', self.opcode, 0, self.addr, 0x0, self.length, bytes(7))


class RKCBW:
    __slots__ = ['signature', 'tag', 'tx_len', 'flags', 'lun', 'cb_len', 'cb']

    def __init__(self, tx_len: int, cb_opcode: int):
        self.signature = CBW_SIGNATURE
        self.tag = randint(0, 2**32 - 1)
        self.tx_len = tx_len
        self.flags = USB_OPCODE_DIR[USB_OPERATION_CODES[cb_opcode]]
        self.cb_len = USB_OPCODE_CBLEN[USB_OPERATION_CODES[cb_opcode]]
        self.cb = RKCBWCB(cb_opcode, self.cb_len)
        self.lun = 0

    def to_bytes(self) -> bytes:
        cbw = struct.pack('<IIIBBB', self.signature, self.tag, self.tx_len, self.flags,
                          self.lun, self.cb_len)
        return cbw + self.cb.to_bytes()
