"""Tests for the generic service discovery API"""
import unittest

import kvstore
import registry

MASTER0 = {
    'status': 'pending',
    'mem': '2048',
    'cpu': '1',
    'name': 'master0',
    'id': '',
    'address': '',
    'host': '',
    'services': ['service0', 'service1'],
    'disks': {
        'disk1': {
            'origin': '/data/1/instance-jlopez-cdh-5.7.0-1',
            'destination': '/data/1',
            'mode': 'rw',
            },
        'disk2': {
            'origin': '/data/2/instance-jlopez-cdh-5.7.0-1',
            'destination': '/data/2',
            'mode': 'rw',
            },
        },
}

SLAVE0 = {
    'status': 'pending',
    'mem': '2048',
    'cpu': '1',
    'name': 'slave0.local',
    'id': '',
    'address': '',
    'host': '',
    'services': ['service1'],
    'disks': {
        'disk1': {
            'origin': '/data/1/instance-jlopez-cdh-5.7.0-1',
            'destination': '/data/1',
            'mode': 'rw',
            },
        'disk2': {
            'origin': '/data/2/instance-jlopez-cdh-5.7.0-1',
            'destination': '/data/2',
            'mode': 'rw',
            },
        },
}

SLAVE1 = {
    'status': 'deployed',
    'mem': '2048',
    'cpu': '1',
    'name': 'slave1.local',
    'id': '1a2b3c4e',
    'address': '10.112.200.101',
    'host': 'c13-1.local',
    'services': ['service1'],
}

SERVICE0 = {
    'status': 'pending',
    'nodes': ['master0'],
    'heap': '2048',
    'workers': '11',
}

SERVICE1 = {
    'status': 'pending',
    'nodes': ['slave0', 'slave1'],
    'heap': '2048',
    'disks': '11',
}

PREFIX = 'clusters'
USER = 'user'
PRODUCT = 'product'
VERSION = '1.0.0'
BASEDN = '{}/{}/{}/{}'.format(PREFIX, USER, PRODUCT, VERSION)

REGISTRY = {PREFIX: { USER: { PRODUCT: { VERSION: {
    'cluster1': {
        'nodes': {
            'master0': MASTER0,
            'slave0': SLAVE0,
            'slave1': SLAVE1
        },
        'services': {
            'service0': SERVICE0,
            'service1': SERVICE1
        },
        'status': 'running'
}}}}}}


class KVMock(object):
    """Mock KV store for testing"""
    def __init__(self, data):
        self._data = data

    def get(self, key):
        key = key.strip('/')
        fields = key.split('/')
        value = self._data
        for f in fields:
            value = value[f]
        return value

    def set(self, key, value):
        key = key.strip('/')
        fields = key.split('/')
        prop = self._data
        for f in fields[:-1]:
            try:
                prop = prop[f]
            except KeyError:
                prop[f] = {}
                prop = prop[f]
        prop[fields[-1]] = value

    def recurse(self, key):
        key = key.strip('/')
        fields = key.split('/')
        subtree = self._data
        for f in fields:
            try:
                subtree = subtree[f]
            except KeyError:
                raise kvstore.KeyDoesNotExist
        result = {}
        for e in subtree:
            result['{0}/{1}'.format(key, e)] = ''
        return result

    def delete(self, key, recursive=False):
        if not recursive:
            raise NotImplementedError
        key = key.strip('/')
        fields = key.split('/')
        prop = self._data
        for f in fields[:-1]:
            prop = prop[f]
        del prop[fields[-1]]


class RegistryNodeTestCase(unittest.TestCase):

    def setUp(self):
        REGISTRY_COPY = REGISTRY.copy()
        # Mock internal kvstore in the registry
        registry._kv = KVMock(REGISTRY_COPY)

    def tearDown(self):
        pass

    def test_get_node_status(self):
        node = registry.Node(BASEDN + '/cluster1/nodes/master0')
        expected = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['nodes']['master0']['status']
        status = node.status
        self.assertEqual(status, expected)

    def test_set_node_status(self):
        node = registry.Node(BASEDN + '/cluster1/nodes/master0')
        node.status = 'configured'
        self.assertEqual(node.status, 'configured')

    def test_get_node_name(self):
        node = registry.Node(BASEDN + '/cluster1/nodes/master0')
        expected = 'master0'
        name = node.name
        self.assertEqual(name, expected)

    def test_set_node_name_not_allowed(self):
        node = registry.Node(BASEDN + '/cluster1/nodes/master0')
        with self.assertRaises(registry.ReadOnlyAttributeError):
            node.name = 'new.local'

    def test_get_node_services(self):
        basedn = BASEDN + '/cluster1/nodes/master0'
        basedn_services = BASEDN + '/cluster1/services'
        node = registry.Node(basedn)
        services = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['nodes']['master0']['services']
        expected = [
            registry.Service('{}/{}'.format(basedn_services, n)) for n in services]
        self.assertEqual(sorted(node.services), sorted(expected))

    def test_get_node_disks(self):
        basedn = BASEDN + '/cluster1/nodes/master0'
        basedn_disks = basedn + '/disks'
        node = registry.Node(basedn)
        disks = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['nodes']['master0']['disks'].keys()
        expected = [
            registry.Disk('{}/{}'.format(basedn_disks, d)) for d in disks]
        self.assertEqual(sorted(node.disks), sorted(expected))

    def test_get_cluster_instance(self):
        basedn = BASEDN + '/cluster1/nodes/master0'
        node = registry.Node(basedn)
        cluster = node.cluster
        expected = registry.Cluster(BASEDN + '/cluster1')
        self.assertEqual(cluster, expected)


class RegistryServiceTestCase(unittest.TestCase):

    def setUp(self):
        REGISTRY_COPY = REGISTRY.copy()
        # Mock internal kvstore in the registry
        registry._kv = KVMock(REGISTRY_COPY)

    def tearDown(self):
        pass

    def test_get_service_status(self):
        service = registry.Service(BASEDN + '/cluster1/services/service0')
        expected = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['services']['service0']['status']
        status = service.status
        self.assertEqual(status, expected)

    def test_set_service_status(self):
        service = registry.Service(BASEDN + '/cluster1/services/service0')
        service.status = 'configured'
        self.assertEqual(service.status, 'configured')

    def test_get_service_heap(self):
        service = registry.Service(BASEDN + '/cluster1/services/service0')
        expected = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['services']['service0']['heap']
        heap = service.heap
        self.assertEqual(heap, expected)

    def test_set_service_heap(self):
        service = registry.Service(BASEDN + '/cluster1/services/service0')
        expected = '1234'
        service.heap = expected
        self.assertEqual(service.heap, expected)

    def test_get_service_nodes(self):
        basedn = BASEDN + '/cluster1/services/service0'
        basedn_nodes = BASEDN + '/cluster1/nodes'
        service = registry.Service(basedn)
        nodes = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['services']['service0']['nodes']
        expected = [
            registry.Node('{}/{}'.format(basedn_nodes, n)) for n in nodes]
        self.assertEqual(sorted(service.nodes), sorted(expected))


class RegistryClusterTestCase(unittest.TestCase):

    def setUp(self):
        REGISTRY_COPY = REGISTRY.copy()
        # Mock internal kvstore in the registry
        registry._kv = KVMock(REGISTRY_COPY)

    def tearDown(self):
        pass

    def test_get_cluster_status(self):
        cluster = registry.Cluster(BASEDN + '/cluster1')
        expected = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['status']
        status = cluster.status
        self.assertEqual(status, expected)

    def test_get_cluster_nodes(self):
        cluster = registry.Cluster(BASEDN + '/cluster1')
        nodes = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['nodes'].keys()
        expected = [
            registry.Node('{}/cluster1/nodes/{}'.format(BASEDN, e)) for e in nodes]
        self.assertEqual(sorted(cluster.nodes), sorted(expected))

    def test_get_cluster_services(self):
        cluster = registry.Cluster(BASEDN + '/cluster1')
        services = REGISTRY[PREFIX][USER][PRODUCT][VERSION]['cluster1']['services'].keys()
        expected = [registry.Service('{}/cluster1/services/{}'.format(BASEDN, e)) for e in services]
        self.assertEqual(sorted(cluster.services), sorted(expected))


class RegistryRegistrationTestCase(unittest.TestCase):

    def setUp(self):
        REGISTRY_COPY = REGISTRY.copy()
        # Mock internal kvstore in the registry
        registry._kv = KVMock(REGISTRY_COPY)

    def tearDown(self):
        pass

    def test_parse_id(self):
        route = 'instances/jlopez/cdh/5.7.0/99/nodes/master0/status'
        prefix = 'instances/jlopez/cdh/5.7.0'
        iid = registry._parse_id(route, prefix)
        self.assertEqual(iid, 99)


class RegistryUtilsTestCase(unittest.TestCase):

    def setUp(self):
        REGISTRY_COPY = REGISTRY.copy()
        # Mock internal kvstore in the registry
        registry._kv = KVMock(REGISTRY_COPY)

    def tearDown(self):
        pass

    def test_parse_cluster_dn_four_fields(self):
        dn = 'clusters/user/cdh/5.7.0/1/nodes/node0/services/service1/property'
        expected = 'clusters/user/cdh/5.7.0/1'
        result = registry._parse_cluster_dn(dn)
        self.assertEqual(result, expected)

    def test_parse_cluster_dn_one_field(self):
        dn = 'clusters/user/cdh/5.7.0/cluster1/'
        expected = 'clusters/user/cdh/5.7.0/cluster1'
        result = registry._parse_cluster_dn(dn)
        self.assertEqual(result, expected)

    def test_parse_disk_middle(self):
        dn = 'instances/cdh/5.7.0/1/nodes/node0/disks/disk99/mode'
        expected = 'instances/cdh/5.7.0/1/nodes/node0/disks/disk99'
        result = registry._parse_disk(dn)
        self.assertEqual(result, expected)

    def test_parse_disk_end(self):
        dn = 'instances/cdh/5.7.0/1/nodes/node0/disks/disk99'
        expected = 'instances/cdh/5.7.0/1/nodes/node0/disks/disk99'
        result = registry._parse_disk(dn)
        self.assertEqual(result, expected)

    def test_id_from(self):
        dn = 'instances/cdh/5.7.0/1/nodes/node0/disks/disk99'
        expected = 'instances--cdh--5__7__0--1--nodes--node0--disks--disk99'
        result = registry.id_from(dn)
        self.assertEqual(result, expected)

    def test_dn_from(self):
        id = 'instances--cdh--5__7__0--1--nodes--node0--disks--disk99'
        expected = 'instances/cdh/5.7.0/1/nodes/node0/disks/disk99'
        result = registry.dn_from(id)
        self.assertEqual(result, expected)

    def test_parse_name(self):
        dn = 'instances/cdh/5.7.0/1/nodes/node0/disks/disk99'
        expected = 'disk99'
        result = registry.parse_name(dn)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
