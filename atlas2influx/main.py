#!/usr/bin/env python
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


import sys, random, geohash
import argparse
from threading import Thread
import yaml, requests, json
from ripe.atlas.cousteau import AtlasStream
from influxdb import InfluxDBClient


class Stream(Thread):
    def __init__(self, db_client, channel, stream_type, parameters):
        Thread.__init__(self)
        self.db_client = db_client
        self.channel = channel
        self.stream_type = stream_type
        self.parameters = parameters
        self.probes = {}
        self.geohash = {}

    def on_result_ping(self, ping):
        if self.db_client:
            try:
                if not self.probes.has_key(ping["prb_id"]):
                    data = requests.get("https://atlas.ripe.net/api/v2/probes/%s" % ping["prb_id"])
                    if data.status_code == 200:
                        self.probes[ping["prb_id"]] = data.json()
                        try:
                            self.geohash[ping["prb_id"]] = geohash.encode(data.json()["geometry"]["coordinates"][1], data.json()["geometry"]["coordinates"][0])
                        except:
                            print "Failed on ", data.json()["geometry"]["coordinates"]

                json_body = [
                    {
                        "measurement": "ping_avg",
                        "tags": {
                            "prb_id": "{}".format(ping['prb_id']),
                            "msm_id": "{}".format(ping['msm_id']),
                            "src_addr": "{}".format(ping['src_addr']),
                            "dst_addr": "{}".format(ping['dst_addr']),
                            "country" : self.probes[ping["prb_id"]].get("country_code", ""),
                            "asn" : self.probes[ping["prb_id"]].get("asn_v4", 0),
                            "geohash" : "{}".format(self.geohash[ping["prb_id"]]),
                        },
                        # convert time into nanoseconds
                        "time": int(ping['timestamp']) * (10**9),
                        "fields": {
                            "value": float(ping['avg'])
                        }
                    },
                    {
                        "measurement": "ping_loss",
                        "tags": {
                            #"prb_id": "{}".format(ping['prb_id']),
                            #"msm_id": "{}".format(ping['msm_id']),
                            "src_addr": "{}".format(ping['src_addr']),
                            "dst_addr": "{}".format(ping['dst_addr']),
                            "country" : self.probes[ping["prb_id"]]["country_code"],
                            "asn" : self.probes[ping["prb_id"]].get("asn_v4", 0),
                            "geohash" : "{}".format(self.geohash[ping["prb_id"]]),
                        },
                        # convert time into nanoseconds
                        "time": int(ping['timestamp']) * (10**9),
                        "fields": {
                            "value": int(ping["sent"])-int(ping["rcvd"]),
                        }
                    },
                ]
                self.db_client.write_points(json_body)
            except KeyError:
                pass

    def on_result_response(self, *args):
        """
        Function that will be called every time we receive a new result.
        Args is a tuple, so you should use args[0] to access the real message.
        """
        if args[0]['type'] == 'ping':
            self.on_result_ping(args[0])
        else:
            try:
                sys.stderr.write(
                    'Measurement type {} not supported.\n'.format(
                        args[0]['type']
                    )
                )
                sys.stderr.write('{}\n'.format(args[0]))
            except KeyError as err:
                sys.stderr.write(
                    str('Unexpected key {} in result.\n'.format(err))
                )

    def run(self):
        """
        Function which adds a new stream.
        """
        atlas_stream = AtlasStream()
        atlas_stream.connect()

        atlas_stream.bind_channel(
            self.channel,
            self.on_result_response,
        )
        atlas_stream.start_stream(
            stream_type=self.stream_type,
            **self.parameters
        )

        atlas_stream.timeout()
        atlas_stream.disconnect()


def main():
    threads = []

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

    # Start InfluxDB client
    try:
        db_client = InfluxDBClient(
            '{}'.format(config['db']['host']),
            '{}'.format(config['db']['port']),
            '{}'.format(config['db']['user']),
            '{}'.format(config['db']['password']),
            '{}'.format(config['db']['database']),
        )
    except KeyError as err:
        sys.stderr.write(
            'ERROR: config db missing key {}.\n'.format(
                err,
            )
        )
        sys.exit(1)

    # Create a thread per stream
    for msm in config['measurements']:
        thread = Stream(
            db_client,
            'atlas_result',
            'result',
            {'msm': msm},
        )
        threads.append(thread)

    # Start all streams
    for thread in threads:
        thread.daemon = True
        thread.start()

    try:
        # Stop all streams
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        pass

    sys.exit(0)


if __name__ == '__main__':
    main()
