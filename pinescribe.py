#!/usr/bin/env python3
import click
import usb1
from pprint import pprint
from scribe import *


@click.group()
def main():
    pass


@main.command()
def list_devices():
    devs = usb.scan_devices()

    for d in devs:
        click.echo(f'{d.vendor_id:04x}:{d.product_id:04x}'
                   f' on bus {d.bus:03d} addr {d.dev_addr:03d}: {d.dev_type}')


@main.command()
@click.argument('loader', type=click.File('rb'))
def download_boot(loader):
    try:
        ldr_header = bootfile.parse_header(loader)
        pprint(ldr_header, sort_dicts=False)
    except bootfile.BootfileException as e:
        click.echo(f"Error parsing loader: {e}", err=True)
        return -1
    entries = ldr_header["entries"]["471"] + ldr_header["entries"]["472"]
    for e in entries:
        e.read_payload(loader)
    with usb1.USBContext() as uc:
        try:
            handle = usb.get_device(uc)
        except usb.DeviceException as e:
            click.echo(f"Error opening device: {e}", err=True)
            return -2
        for e in entries:
            click.echo(f"Downloading {e.name}...")
            try:
                usb.download_loader(handle, e)
            except usb1.USBErrorNoDevice as e:
                click.echo("Unfortunately, we got disconnected during a download", err=True)
                return -3
            click.echo("Download finished")


if __name__ == '__main__':
    main()
