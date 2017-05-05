"""
---------
NFV steps
---------
"""

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import xml.etree.ElementTree as ElementTree

from hamcrest import (assert_that, equal_to, is_not, greater_than,
                      has_length, has_key)  # noqa

from stepler.third_party import steps_checker

__all__ = [
    'NfvSteps'
]


class NfvSteps(object):
    """NFV steps."""

    @steps_checker.step
    def get_cpu_mem_numa_values(self, host_cpus, host_mem, case):
        """Step to get flavor parameters for normal and wrong cases.

        Args:
            host_cpus (dict): cpu distribution values, ex:
                {'numa0': [0, 1, 2], 'numa1': [3]}
            host_mem (dict): memory distribution values, ex:
                {'numa0': 2048, 'numa1': 2048}
            case (str): case, can be 'normal', 'wrong_cpu' or 'wrong_memory'

        Returns:
            tuple: (vcpus, ram, cpu_numa0, cpu_numa1, mem_numa0, mem_numa1),
                cpu_numa values are str, other values are int

        Raises:
            AssertionError: if NUMA count <= 1 or inconsistent input data
        """
        def _get_flavor_cpus(cpus_list):
            # Convert cpus list to string (format for flavor metadata)
            flv_cpus = ','.join([str(i) for i in cpus_list])
            return flv_cpus

        assert_that(host_cpus, has_length(greater_than(1)))
        assert_that(len(host_cpus), equal_to(len(host_mem)))

        vcpus = len(host_cpus['numa0']) + len(host_cpus['numa1'])
        host_mem0 = math.ceil(host_mem['numa0'] / 1024)
        host_mem1 = math.ceil(host_mem['numa1'] / 1024)

        if case == 'normal':
            correct_cnt = len(host_cpus['numa0'])
            cpu_numa0 = _get_flavor_cpus(range(vcpus)[:correct_cnt])
            cpu_numa1 = _get_flavor_cpus(range(vcpus)[correct_cnt:])
            mem_numa0 = 512
            mem_numa1 = 1536
        elif case == 'wrong_cpu':
            # allocate more cpus than available
            cnt_to_exceed = len(host_cpus['numa0']) + 1
            cpu_numa0 = _get_flavor_cpus(range(vcpus)[:cnt_to_exceed])
            cpu_numa1 = _get_flavor_cpus(range(vcpus)[cnt_to_exceed:])
            mem_numa0 = int(host_mem0 / 2)
            mem_numa1 = int(host_mem1 / 2)
        else:
            # allocate more memory than available
            correct_cnt = len(host_cpus['numa0'])
            cpu_numa0 = _get_flavor_cpus(range(vcpus)[:correct_cnt])
            cpu_numa1 = _get_flavor_cpus(range(vcpus)[correct_cnt:])
            mem_numa0 = int(max(host_mem0, host_mem1) +
                            min(host_mem0, host_mem1) / 2)
            mem_numa1 = int(min(host_mem0, host_mem1) / 2)

        ram = mem_numa0 + mem_numa1
        return (vcpus, ram, cpu_numa0, cpu_numa1, mem_numa0, mem_numa1)

    @steps_checker.step
    def check_cpu_for_server(self, server_dump, numa_count, host_cpus,
                             exp_vcpupin=None):
        """Step to check vcpus allocation for server.

        Vcpus should be on the same numa node if flavor metadata
        'hw:numa_nodes':1 or on different numa nodes if 'hw:numa_nodes':2

        Args:
            server_dump (str): server dump (result of 'virsh dumpxml')
            numa_count (int): numa count
            host_cpus (dict): cpu distribution values, ex:
                {'numa0': [0, 1, 2], 'numa1': [3]}
            exp_vcpupin (dict, optional): vcpu distribution per numa node, ex:
                {'numa0': [0, 1, 2], 'numa1': [3]}

        Raises:
            AssertionError: if unexpected CPU values in server dump
        """
        root = ElementTree.fromstring(server_dump)
        actual_numa = root.find('numatune').findall('memnode')
        assert_that(actual_numa, has_length(numa_count),
                    "Unexpected count of numa nodes")

        vm_vcpupins = [
            {'id': int(v.get('vcpu')), 'set_id': int(v.get('cpuset'))}
            for v in root.find('cputune').findall('vcpupin')]
        vm_vcpus = [vcpupin['set_id'] for vcpupin in vm_vcpupins]
        used_numa_count = 0
        for cpus in host_cpus.values():
            if set(cpus) & set(vm_vcpus):
                used_numa_count += 1
        assert_that(used_numa_count, equal_to(numa_count),
                    "Unexpected count of numa nodes in use")

        if exp_vcpupin is not None:
            act_vcpupin = {}
            for numa, ids in host_cpus.items():
                pins = [p['id'] for p in vm_vcpupins if p['set_id'] in ids]
                act_vcpupin.update({numa: pins})
            assert_that(act_vcpupin, equal_to(exp_vcpupin),
                        "Unexpected cpu allocation")

    @steps_checker.step
    def check_memory_allocation(self, server_dump, numa_count, exp_mem):
        """Step to check memory allocation for server.

        Args:
            server_dump (str): server dump (result of 'virsh dumpxml')
            numa_count (int): numa count
            exp_mem (dict): memory distribution values, ex:
                {'0': 2048, '1': 2048}

        Raises:
            AssertionError: if unexpected memory values in server dump
        """
        root = ElementTree.fromstring(server_dump)
        numa_cells = root.find('cpu').find('numa').findall('cell')
        assert_that(numa_cells, has_length(numa_count),
                    "Unexpected count of numa nodes")
        memory_allocation = {cell.get('id'): int(cell.get('memory')) / 1024
                             for cell in numa_cells}
        assert_that(memory_allocation, equal_to(exp_mem),
                    "Unexpected memory allocation")

    @steps_checker.step
    def check_server_page_size(self, server_dump, exp_size):
        """Step to check server page size.

        Args:
            server_dump (str): server dump (result of 'virsh dumpxml')
            exp_size (int): expected page size on server

        Raises:
            AssertionError: if unexpected page size in server dump
        """
        root = ElementTree.fromstring(server_dump)
        if exp_size is None:
            assert_that(root.find('memoryBacking'), equal_to(None),
                        "Unexpected element 'memoryBacking' in server dump")
        else:
            assert_that(root.find('memoryBacking'), is_not(equal_to(None)),
                        "Element 'memoryBacking' is not found in server dump")
            page_size = int(root.find('memoryBacking').find('hugepages').find(
                'page').get('size'))
            assert_that(page_size, equal_to(exp_size),
                        "Unexpected page size")

    @steps_checker.step
    def check_hugepage_diff(self, hp_data_old, hp_data_new, diff_hps):
        """Step to check differences between old and new HP sizes on computes.

        Total sizes are constant, but free sizes can be changed, and
        differences must be equal to expected values.

        Args:
            hp_data_old (list): list [[fqdn1, hp_data1] ...], where
                hp_data - dict like {2048: {'nr': 1024, 'free': 512},
                                     1048576: {'nr': 0, 'free': 0}
            hp_data_new (list): list of the same structure
            diff_hps (dict): differences between old and new states, ex:
                {fqdn1: {2048: 512}, fqdn2: {2048: 256}}

        Raises:
            AssertionError: if unexpected size values or some inconsistency
                between old, new data and expected differences
        """
        data_old = dict(hp_data_old)
        data_new = dict(hp_data_new)

        for fqdn in data_old:
            assert_that(data_new, has_key(fqdn))
            assert_that(len(data_new[fqdn]), equal_to(len(data_old[fqdn])))
            for size in data_old[fqdn]:
                assert_that(data_new[fqdn], has_key(size))
                assert_that(data_new[fqdn][size]['nr'],
                            equal_to(data_old[fqdn][size]['nr']),
                            'unexpected change of total memory')
                if fqdn in diff_hps and size in diff_hps[fqdn]:
                    assert_that(data_old[fqdn][size]['nr'],
                                is_not(equal_to(0)),
                                'some differences are expected for hosts'
                                ' without HP of size={}'.format(size))
                    assert_that(data_new[fqdn][size]['free'],
                                equal_to(data_old[fqdn][size]['free'] -
                                         diff_hps[fqdn][size]),
                                'unexpected value of free memory')
                else:
                    assert_that(data_new[fqdn][size]['free'],
                                equal_to(data_old[fqdn][size]['free']),
                                'unexpected change of free memory')
