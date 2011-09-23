# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and

import sys
import httplib
import unittest

from libcloud.common.linode import LinodeException
from libcloud.dns.types import RecordType, ZoneDoesNotExistError
from libcloud.dns.drivers.linode import LinodeDNSDriver

from test import MockHttp # pylint: disable-msg=E0611
from test.file_fixtures import DNSFileFixtures # pylint: disable-msg=E0611
from test.secrets import DNS_PARAMS_LINODE

DOES_NOT_EXIST_ERROR = '{"ERRORARRAY":[{"ERRORCODE":5,"ERRORMESSAGE":"Object not found"}],"DATA":{},"ACTION":"domain.resource.list"}'

class LinodeTests(unittest.TestCase):
    def setUp(self):
        LinodeDNSDriver.connectionCls.conn_classes = (
                None, LinodeMockHttp)
        LinodeMockHttp.use_param = 'api_action'
        LinodeMockHttp.type = None
        self.driver = LinodeDNSDriver(*DNS_PARAMS_LINODE)

    def assertHasKeys(self, dictionary, keys):
        for key in keys:
            self.assertTrue(key in dictionary, 'key "%s" not in dictionary' %
                            (key))

    def test_list_zones_success(self):
        zones = self.driver.list_zones()
        self.assertEqual(len(zones), 2)

        zone = zones[0]
        self.assertEqual(zone.id, '5093')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.domain, 'linode.com')
        self.assertEqual(zone.ttl, None)
        self.assertHasKeys(zone.extra, ['description', 'soa_email', 'status'])

    def test_list_records_success(self):
        zone = self.driver.list_zones()[0]
        records = self.driver.list_records(zone=zone)
        self.assertEqual(len(records), 2)

        record = records[0]
        self.assertEqual(record.id, '28536')
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '75.127.96.245')
        self.assertHasKeys(record.extra, ['protocol', 'ttl_sec', 'port', 'weight'])

    def test_list_records_zone_does_not_exist(self):
        zone = self.driver.list_zones()[0]

        LinodeMockHttp.type = 'ZONE_DOES_NOT_EXIST'
        try:
            records = self.driver.list_records(zone=zone)
        except ZoneDoesNotExistError, e:
            self.assertEqual(e.zone_id, zone.id)
        else:
            self.fail('Exception was not thrown')

    def test_get_zone_success(self):
        LinodeMockHttp.type = 'GET_ZONE'

        zone = self.driver.get_zone(zone_id='5093')
        self.assertEqual(zone.id, '5093')
        self.assertEqual(zone.type, 'master')
        self.assertEqual(zone.domain, 'linode.com')
        self.assertEqual(zone.ttl, None)
        self.assertHasKeys(zone.extra, ['description', 'soa_email', 'status'])

    def test_get_zone_does_not_exist(self):
        LinodeMockHttp.type = 'GET_ZONE_DOES_NOT_EXIST'

        try:
            zone = self.driver.get_zone(zone_id='4444')
        except ZoneDoesNotExistError, e:
            self.assertEqual(e.zone_id, '4444')
        else:
            self.fail('Exception was not thrown')

    def test_get_record_success(self):
        LinodeMockHttp.type = 'GET_RECORD'
        record = self.driver.get_record(zone_id='1234', record_id='28536')
        self.assertEqual(record.id, '28536')
        self.assertEqual(record.name, 'www')
        self.assertEqual(record.type, RecordType.A)
        self.assertEqual(record.data, '75.127.96.245')
        self.assertHasKeys(record.extra, ['protocol', 'ttl_sec', 'port', 'weight'])

    def test_get_record_zone_does_not_exist(self):
        LinodeMockHttp.type = 'GET_RECORD_ZONE_DOES_NOT_EXIST'

        try:
            record = self.driver.get_record(zone_id='444', record_id='28536')
        except ZoneDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_get_record_record_does_not_exist(self):
        LinodeMockHttp.type = 'GET_RECORD_RECORD_DOES_NOT_EXIST'

        try:
            record = self.driver.get_record(zone_id='444', record_id='28536')
        except ZoneDoesNotExistError:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_zone_success(self):
        zone = self.driver.create_zone(domain='foo.bar.com', type='master',
                                       ttl=None, extra=None)
        self.assertEqual(zone.id, '5123')
        self.assertEqual(zone.domain, 'foo.bar.com')

    def test_create_zone_validaton_error(self):
        LinodeMockHttp.type = 'VALIDATION_ERROR'

        try:
            zone = self.driver.create_zone(domain='foo.bar.com', type='master',
                                           ttl=None, extra=None)
        except LinodeException:
            pass
        else:
            self.fail('Exception was not thrown')

    def test_create_record_success(self):
        pass

    def test_update_record_success(self):
        pass

    def test_delete_record_success(self):
        pass

    def test_delete_record_does_not_exist(self):
        pass

    def test_delete_zone_success(self):
        pass

    def test_delete_zone_does_not_exist(self):
        pass


class LinodeMockHttp(MockHttp):
    fixtures = DNSFileFixtures('linode')

    def _domain_list(self, method, url, body, headers):
        body = self.fixtures.load('domain_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_resource_list(self, method, url, body, headers):
        body = self.fixtures.load('resource_list.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _ZONE_DOES_NOT_EXIST_domain_resource_list(self, method, url, body, headers):
        body = DOES_NOT_EXIST_ERROR
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_ZONE_domain_list(self, method, url, body, headers):
        body = self.fixtures.load('get_zone.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_ZONE_DOES_NOT_EXIST_domain_list(self, method, url, body, headers):
        body = self.fixtures.load('get_zone_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_domain_list(self, method, url, body, headers):
        body = self.fixtures.load('get_zone.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_domain_resource_list(self, method, url, body, headers):
        body = self.fixtures.load('get_record.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_ZONE_DOES_NOT_EXIST_domain_list(self, method, url, body, headers):
        body = self.fixtures.load('get_zone_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _GET_RECORD_RECORD_DOES_NOT_EXIST_domain_list(self, method, url, body, headers):
        body = self.fixtures.load('get_record_does_not_exist.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _domain_create(self, method, url, body, headers):
        body = self.fixtures.load('create_domain.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])

    def _VALIDATION_ERROR_domain_create(self, method, url, body, headers):
        body = self.fixtures.load('create_domain_validation_error.json')
        return (httplib.OK, body, {}, httplib.responses[httplib.OK])


if __name__ == '__main__':
    sys.exit(unittest.main())