import usb1


ROCKCHIP_VENDOR_ID = 0x2207
PRODUCT_IDS = [
    0x350a,
]

class RKUSBDevice:
    __slots__ = ['product_id', 'vendor_id', 'dev_type',
                 'bus', 'dev_addr']

    def bcd_to_dev_type(bcd) -> str:
        t = bcd & 0x1;
        return 'maskrom' if t == 0 else 'loader'

    def __init__(self, device: usb1.USBDevice):
        self.product_id = device.getProductID()
        self.vendor_id = device.getVendorID()
        self.dev_type = RKUSBDevice.bcd_to_dev_type(device.getbcdUSB())
        self.bus = device.getBusNumber()
        self.dev_addr = device.getDeviceAddress()


def scan_devices():
    devices = []

    with usb1.USBContext() as uc:
        for d in uc.getDeviceIterator(uc):
            if d.getVendorID() == ROCKCHIP_VENDOR_ID:
                if d.getProductID() in PRODUCT_IDS:
                    devices.append(RKUSBDevice(d))

    return devices
