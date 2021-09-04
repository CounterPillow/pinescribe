import click
from time import sleep
import usb1
from . import bootfile, cbw


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


def get_device(uc: usb1.USBContext, maskrom_only=True) -> usb1.USBDeviceHandle:
    for i in PRODUCT_IDS:
        dev = uc.getByVendorIDAndProductID(ROCKCHIP_VENDOR_ID, i)
        if dev:
            if maskrom_only:
                if RKUSBDevice.bcd_to_dev_type(dev.getbcdUSB()) == 'maskrom':
                    break
            else:
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


# FIXME: doesn't check CSW signature/tag match right now
def get_flash_info(handle: usb1.USBDeviceHandle):
    c = cbw.RKCBW(11, cbw.USB_OPERATION_CODE_VALUES['READ_FLASH_INFO'])

    chosen_ep_out = 0
    chosen_ep_in = 0
    iface_num_out = 0
    iface_num_in = 0
    for iface in handle.getDevice().iterSettings():
        for ep in iface:
            addr = ep.getAddress()
            if addr & 0x80 == 0:
                if not chosen_ep_out:
                    chosen_ep_out = addr
                    iface_num_out = iface.getNumber()
            if addr == 0:
                if not chosen_ep_in:
                    chosen_ep_in = addr
                    iface_num_in = iface.getNumber()

    with handle.claimInterface(iface_num_out):
        handle.bulkWrite(chosen_ep_out, c.to_bytes())
    with handle.claimInterface(iface_num_in):
        resp = handle.bulkRead(chosen_ep_in, 512, 5000)
    if len(resp) == 0:
        raise DeviceException("bulk read didn't return any data")
    return resp
