#!/usr/bin/env python3
import click
from scribe import *


@click.group()
def main():
    pass


@main.command()
def list_devices():
    devs = scanusb.scan_devices()

    for d in devs:
        click.echo(f'{d.vendor_id:04x}:{d.product_id:04x}'
                   f' on bus {d.bus:03d} addr {d.dev_addr:03d}: {d.dev_type}')


@main.command()
@click.argument('loader', type=click.File('rb'))
def download_boot(loader):
    try:
        bootfile.parse_header(loader)
    except bootfile.BootfileException as e:
        click.echo(f"Error parsing loader: {e}", err=True)
        return -1
    devs = scanusb.scan_devices()
    if len(devs) == 0:
        click.echo("No connected devices!", err=True)
        return -2
    if len(devs) > 1:
        click.echo("Too many connected devices", err=True)
        return -3
    if devs[0].dev_type != 'maskrom':
        click.echo("Your connected device isn't in maskrom mode", err=True)
        return -4


if __name__ == '__main__':
    main()
