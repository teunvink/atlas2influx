#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# atlas2influx: This script gets data from RIPE Atlas API and push them to
# a InfluxDB.
# Copyright (C) 2016 Tobias Rueetschi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import argparse
import threading
import yaml
from ripe.atlas.cousteau import AtlasStream
from influxdb import InfluxDBClient


THREADS = []


def on_result_ping(ping):
    print(ping)


def on_result_response(*args):
    """
    Function that will be called every time we receive a new result.
    Args is a tuple, so you should use args[0] to access the real message.
    """
    if args[0]['type'] == 'ping':
        on_result_ping(args[0])
    else:
        try:
            sys.stderr.write(
                'Measurement type {} not supported.\n'.format(
                    args[0]['type']
                )
            )
        except KeyError as err:
            sys.stderr.write(str('Unexpected key {} in result.\n'.format(err)))


def stream(channel, stream_type, parameters):
    """
    Function which adds a new stream.
    """
    atlas_stream = AtlasStream()
    atlas_stream.connect()

    atlas_stream.bind_channel(
        channel,
        on_result_response,
    )
    atlas_stream.start_stream(
        stream_type=stream_type,
        **parameters
    )

    atlas_stream.timeout(seconds=2)
    atlas_stream.disconnect()


def main():
    # Get the configuration
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="This script gets data from RIPE Atlas API and push them"
                    "to a InfluxDB."
    )
    parser.add_argument("-c", "--config",
                        required=False,
                        metavar="FILE",
                        default="config.yml",
                        help="Configuration file")
    argp = parser.parse_args(sys.argv[1:])
    try:
        with open(argp.config, 'r') as file:
            config = yaml.safe_load(file)
    except:
        sys.stderr.write("Load configuration {} failed.\n".format(
            argp.config
        ))
        sys.exit(1)

    if 'measurements' not in config:
        config['measurements'] = []

    # Create a thread per stream
    for msm in config['measurements']:
        thread = threading.Thread(
            target=stream,
            args=(
                'result',
                'result',
                {'msm': msm},
            )
        )
        THREADS.append(thread)

    thread = threading.Thread(
        target=stream,
        args=(
            'probe',
            'probestatus',
            {'enrichProbes': True},
        )
    )
    THREADS.append(thread)

    # Start all streams
    for thread in THREADS:
        thread.start()

    # Stop all streams
    for thread in THREADS:
        thread.join()

    sys.exit(0)


if __name__ == '__main__':
    main()
