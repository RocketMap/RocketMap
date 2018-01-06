import argparse
import json
import time
import random

import utils


class Spawnpoint(object):

    def __init__(self, data):
        # not needed but useful for debugging
        self.spawnpoint_id = data.get('spawnpoint_id') or data.get('sid')

        try:
            self.position = (float(data['latitude']), float(data['longitude']))
        except KeyError:
            self.position = (float(data['lat']), float(data['lng']))

        self.time = data['time']

    def serialize(self):
        obj = dict()

        if self.spawnpoint_id is not None:
            obj['spawnpoint_id'] = self.spawnpoint_id
        obj['latitude'] = self.position[0]
        obj['longitude'] = self.position[1]
        obj['time'] = self.time

        return obj


class Spawncluster(object):

    def __init__(self, spawnpoint):
        self._spawnpoints = [spawnpoint]
        self.centroid = spawnpoint.position
        self.min_time = spawnpoint.time
        self.max_time = spawnpoint.time

    def __getitem__(self, key):
        return self._spawnpoints[key]

    def __iter__(self):
        for x in self._spawnpoints:
            yield x

    def __contains__(self, item):
        return item in self._spawnpoints

    def __len__(self):
        return len(self._spawnpoints)

    def append(self, spawnpoint):
        # update centroid
        f = len(self._spawnpoints) / (len(self._spawnpoints) + 1.0)
        self.centroid = utils.intermediate_point(spawnpoint.position,
                                                 self.centroid, f)

        self._spawnpoints.append(spawnpoint)

        if spawnpoint.time < self.min_time:
            self.min_time = spawnpoint.time

        if spawnpoint.time > self.max_time:
            self.max_time = spawnpoint.time

    def simulate_centroid(self, spawnpoint):
        f = len(self._spawnpoints) / (len(self._spawnpoints) + 1.0)
        new_centroid = utils.intermediate_point(spawnpoint.position,
                                                self.centroid, f)

        return new_centroid


def cost(spawnpoint, cluster, time_threshold):
    distance = utils.distance(spawnpoint.position, cluster.centroid)

    min_time = min(cluster.min_time, spawnpoint.time)
    max_time = max(cluster.max_time, spawnpoint.time)

    if max_time - min_time > time_threshold:
        return float('inf')

    return distance


def check_cluster(spawnpoint, cluster, radius, time_threshold):
    # discard infinite cost or too far away
    if cost(spawnpoint, cluster, time_threshold) > 2 * radius:
        return False

    new_centroid = cluster.simulate_centroid(spawnpoint)

    # we'd be removing ourselves
    if utils.distance(spawnpoint.position, new_centroid) > radius:
        return False

    # we'd be removing x
    if any(utils.distance(x.position, new_centroid) > radius for x in cluster):
        return False

    return True


def cluster(spawnpoints, radius, time_threshold):
    clusters = []

    for p in spawnpoints:
        if len(clusters) == 0:
            clusters.append(Spawncluster(p))
        else:
            c = min(clusters, key=lambda x: cost(p, x, time_threshold))

            if check_cluster(p, c, radius, time_threshold):
                c.append(p)
            else:
                c = Spawncluster(p)
                clusters.append(c)

    return clusters


def test(cluster, radius, time_threshold):
    assert cluster.max_time - cluster.min_time <= time_threshold

    for p in cluster:
        assert utils.distance(p.position, cluster.centroid) <= radius
        assert cluster.min_time <= p.time <= cluster.max_time


def main(args):
    radius = args.radius
    time_threshold = args.time_threshold

    with open(args.filename, 'r') as f:
        rows = json.loads(f.read())

    spawnpoints = [Spawnpoint(x) for x in rows]

    print 'Processing', len(spawnpoints), 'spawnpoints...'

    start_time = time.time()
    clusters = cluster(spawnpoints, radius, time_threshold)
    end_time = time.time()

    print 'Completed in {:.2f} seconds.'.format(end_time - start_time)
    print len(clusters), 'clusters found.'
    print '{:.2f}% compression achieved.'.format(
        100.0 * len(clusters) / len(spawnpoints))

    try:
        for c in clusters:
            test(c, radius, time_threshold)
    except AssertionError:
        print 'error: something\'s seriously broken.'
        raise

    # clusters.sort(key=lambda x: len(x))

    if args.output_clusters:
        rows = []
        for c in clusters:
            row = dict()
            row['spawnpoints'] = [x.serialize() for x in c]
            row['latitude'] = c.centroid[0]
            row['longitude'] = c.centroid[1]
            row['min_time'] = c.min_time
            row['max_time'] = c.max_time
            rows.append(row)

        with open(args.output_clusters, 'w') as f:
            f.write(json.dumps(rows, indent=4, separators=(',', ': ')))

    if args.output_spawnpoints:
        rows = []
        for c in clusters:
            row = dict()
            # pick a random id from a clustered spawnpoint
            # we should probably not do this
            if args.long_keys:
                row['spawnpoint_id'] = random.choice(c).spawnpoint_id
                row['latitude'] = c.centroid[0]
                row['longitude'] = c.centroid[1]
            else:
                row['sid'] = random.choice(c).spawnpoint_id
                row['lat'] = c.centroid[0]
                row['lng'] = c.centroid[1]
            # pick the latest time so earlier spawnpoints have already spawned
            row['time'] = c.max_time
            rows.append(row)

        with open(args.output_spawnpoints, 'w') as f:
            f.write(json.dumps(rows, indent=4, separators=(',', ': ')))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cluster close spawnpoints.')
    parser.add_argument('filename', help='Your spawnpoints.json file.')
    parser.add_argument(
        '-os',
        '--output-spawnpoints',
        help='The filename to write compressed spawnpoints to.')
    parser.add_argument(
        '-oc',
        '--output-clusters',
        help='The filename to write cluster data to.')
    parser.add_argument(
        '-r',
        '--radius',
        type=float,
        help=('Maximum radius (in meters) where spawnpoints are considered ' +
              'close (defaults to 70).'),
        default=70)
    parser.add_argument(
        '-t',
        '--time-threshold',
        type=float,
        help=('Maximum time threshold (in seconds) to consider when ' +
              'clustering (defaults to 180).'),
        default=180)
    parser.add_argument(
        '--long-keys',
        action='store_true',
        help='Uses prettier longer key names in the output spawnpoints.json.')

    args = parser.parse_args()

    main(args)
