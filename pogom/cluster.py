from .utils import distance
from .transform import intermediate_point


class SpawnCluster(object):
    def __init__(self, spawnpoint):
        self._spawnpoints = [spawnpoint]
        self.centroid = (spawnpoint['lat'], spawnpoint['lng'])
        self.min_time = spawnpoint['time']
        self.max_time = spawnpoint['time']
        self.spawnpoint_id = spawnpoint['spawnpoint_id']
        self.appears = spawnpoint['appears']
        self.leaves = spawnpoint['leaves']

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
        self.centroid = self.new_centroid(spawnpoint)

        self._spawnpoints.append(spawnpoint)

        if spawnpoint['time'] < self.min_time:
            self.min_time = spawnpoint['time']

        elif spawnpoint['time'] > self.max_time:
            self.max_time = spawnpoint['time']
            self.spawnpoint_id = spawnpoint['spawnpoint_id']
            self.appears = spawnpoint['appears']
            self.leaves = spawnpoint['leaves']

    def get_score(self, spawnpoint, time_threshold):
        min_time = min(self.min_time, spawnpoint['time'])
        max_time = max(self.max_time, spawnpoint['time'])
        sp_position = (spawnpoint['lat'], spawnpoint['lng'])

        if max_time - min_time > time_threshold:
            return float('inf')
        else:
            return distance(sp_position, self.centroid)

    def new_centroid(self, spawnpoint):
        sp_count = len(self._spawnpoints)
        f = sp_count / (sp_count + 1.0)
        new_centroid = intermediate_point(
            (spawnpoint['lat'], spawnpoint['lng']), self.centroid, f)

        return new_centroid

    def test_spawnpoint(self, spawnpoint, radius, time_threshold):
        # Discard spawn points outside the time frame or too far away.
        if self.get_score(spawnpoint, time_threshold) > 2 * radius:
            return False

        new_centroid = self.new_centroid(spawnpoint)

        # Check if spawn point is within range of the new centroid.
        if (distance((spawnpoint['lat'], spawnpoint['lng']), new_centroid) >
                radius):
            return False

        # Check if cluster's spawn points remain in range of the new centroid.
        if any(distance((x['lat'], x['lng']), new_centroid) >
                radius for x in self._spawnpoints):
            return False

        return True


# Group spawn points with similar spawn times that are close to each other.
def cluster_spawnpoints(spawnpoints, radius=70, time_threshold=240):
    # Initialize cluster list with the first spawn point available.
    clusters = [SpawnCluster(spawnpoints.pop())]
    for sp in spawnpoints:
        # Pick the closest cluster compatible to current spawn point.
        c = min(clusters, key=lambda x: x.get_score(sp, time_threshold))

        if c.test_spawnpoint(sp, radius, time_threshold):
            c.append(sp)
        else:
            c = SpawnCluster(sp)
            clusters.append(c)

    # Output new spawn points from generated clusters. Use the latest time
    # to be sure that every spawn point in the cluster has already spawned.
    result = []
    for c in clusters:
        result.append({
            'spawnpoint_id': c.spawnpoint_id,
            'lat': c.centroid[0],
            'lng': c.centroid[1],
            'time': c.max_time,
            'appears': c.appears,
            'leaves': c.leaves
        })

    return result
