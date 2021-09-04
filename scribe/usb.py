import click
from time import sleep
import usb1
from . import bootfile


ROCKCHIP_VENDOR_ID = 0x2207
PRODUCT_IDS = [
    0x350a,
]


class DownloadException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class DeviceException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class RKUSBDevice:
    __slots__ = ['product_id', 'vendor_id', 'dev_type',
                 'bus', 'dev_addr']

    def bcd_to_dev_type(bcd) -> str:
        t = bcd & 0x1
        return 'maskrom' if t == 0 else 'loader'

    def __init__(self, device: usb1.USBDevice):
        self.product_id = device.getProductID()
        self.vendor_id = device.getVendorID()
        self.dev_type = RKUSBDevice.bcd_to_dev_type(device.getbcdUSB())
        self.bus = device.getBusNumber()
        self.dev_addr = device.getDeviceAddress()


def as_chunks(l, size):
    for i in range(0, len(l), size):
        yield l[i:i + size]


def scan_devices():
    devices = []

    with usb1.USBContext() as uc:
        for d in uc.getDeviceIterator(uc):
            if d.getVendorID() == ROCKCHIP_VENDOR_ID:
                if d.getProductID() in PRODUCT_IDS:
                    devices.append(RKUSBDevice(d))

    return devices


def get_device(uc: usb1.USBContext) -> usb1.USBDeviceHandle:
    for i in PRODUCT_IDS:
        dev = uc.getByVendorIDAndProductID(ROCKCHIP_VENDOR_ID, i)
        if dev:
            if RKUSBDevice.bcd_to_dev_type(dev.getbcdUSB()) == 'maskrom':
                break
    else:
        raise DeviceException("no connected devices")
    return dev.open()


def download_loader(handle: usb1.USBDeviceHandle, entry: bootfile.RKLDREntry):
    request_type = 0
    if isinstance(entry, bootfile.RK471Entry):
        request_type = 0x471
    elif isinstance(entry, bootfile.RK472Entry):
        request_type = 0x472
    else:
        raise DownloadException(f"I don't know how to deal with {type(entry)}!")

    if not entry.has_pld():
        raise DownloadException("Entry does not have its payload read")
    crc = int.to_bytes(entry.crc, 4, 'big')[-2:]
    data = entry.pld + crc
    for packet in as_chunks(data, 4096):
        sent = handle.controlWrite(0x40, 0xC, 0, request_type, packet)
        if sent != len(packet):
            raise DownloadException(f"Wanted to send {len(packet)} bytes, only sent {sent}!")

    sleep(entry.pld_delay / 1000)
    sleep(1)
