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
import yaml
import threading


def stream(ch, type, parameters):
    """
    Function which adds a new stream.
    """
    print('Channel={}; Type={}; Parameters={}'.format(
        ch,
        type,
        parameters,
    ))


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
        with open(argp.config, 'r') as f:
            config = yaml.safe_load(f)
    except:
        sys.stderr.write("Load configuration {} failed.\n".format(
            argp.config
        ))
        sys.exit(1)

    if 'measurements' not in config:
        config['measurements'] = []

    threads = []

    # Create a thread per stream
    for msm in config['measurements']:
        t = threading.Thread(
            target=stream,
            args=(
                'result',
                'result',
                {'msm': msm},
            )
        )
        threads.append(t)

    # Start all streams
    for t in threads:
        t.start()

    # Stop all streams
    for t in threads:
        t.join()

    sys.exit(0)


if __name__ == '__main__':
    main()
