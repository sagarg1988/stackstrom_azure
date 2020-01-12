import os
# from st2common.runners.base_action import Action
# from smtplib import SMTP
# from email.header import Header
# from email.mime.application import MIMEApplication
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from haikunator import Haikunator

haikunator = Haikunator()
# Azure Datacenter
LOCATION = 'Southeast Asia'

# Resource Group
GROUP_NAME = 'azure-group'

# Network
VNET_NAME = 'azure-vnet'
SUBNET_NAME = 'azure-subnet'

# VM
OS_DISK_NAME = 'Cloudera-CentOS-OS-Image'
STORAGE_ACCOUNT_NAME = haikunator.haikunate(delimiter='')

IP_CONFIG_NAME = '203.18.137.2'
NIC_NAME = 'azure-linux-nic'
W_NIC_NAME = 'azure-windows-nic'
USERNAME = 'mukeshkumar5375N'
PASSWORD = 'nihilent@123'
VM_NAME = 'Linux-VM'
W_VM_NAME = 'Windows-VM'

VM_REFERENCE = {
    'linux': {
        'publisher': 'Canonical',
        'offer': 'UbuntuServer',
        'sku': '16.04.0-LTS',
        'version': 'latest'
    },
    'windows': {
        'publisher': 'MicrosoftWindowsServer',
        'offer': 'WindowsServer',
        'sku': '2016-Datacenter',
        'version': 'latest'
    }
}

def run():

    subscription_id = os.environ.get(
        'AZURE_SUBSCRIPTION_ID',
        'ef80a466-7372-49e9-b247-57b95886881c')
    credentials = ServicePrincipalCredentials(
        client_id='445a1911-819a-41e8-a093-adfd66ca5ccd',
        secret='rJ--cHsg@=fucrddh3svx1VUe91q2h1N',
        tenant='8ee0f3e4-b788-4efa-bd84-e6bfe7fe9943'
    )
    resource_client = ResourceManagementClient(credentials, subscription_id)
    compute_client = ComputeManagementClient(credentials, subscription_id)
    storage_client = StorageManagementClient(credentials, subscription_id)
    network_client = NetworkManagementClient(credentials, subscription_id)

    ###########
    # Prepare #
    ###########

    import ipdb
    ipdb.set_trace()
    # Create Resource group
    print('\nCreate Resource Group')
    resource_client.resource_groups.create_or_update(
        GROUP_NAME, {'location': LOCATION})

    # Create a storage account
    print('\nCreate a storage account')
    storage_async_operation = storage_client.storage_accounts.create(
        GROUP_NAME,
        STORAGE_ACCOUNT_NAME,
        {
            'sku': {'name': 'standard_lrs'},
            'kind': 'storage',
            'location': LOCATION
        }
    )
    storage_async_operation.wait()
    create_vnet(network_client)
    create_subnet(network_client)
    # Create a NIC
    nic = create_nic(network_client,NIC_NAME)
    # Create Linux VM
    print('\nCreating Linux Virtual Machine')
    vm_parameters = create_vm_parameters(nic.id, VM_REFERENCE['linux'],VM_NAME)
    async_vm_creation = compute_client.virtual_machines.create_or_update(
        GROUP_NAME, VM_NAME, vm_parameters)
    async_vm_creation.wait()
    # Start the VM
    print('\nStart Linux Virtual Machine')
    async_vm_start = compute_client.virtual_machines.start(GROUP_NAME, VM_NAME)
    async_vm_start.wait()

    # Create a NIC
    nic = create_nic(network_client, W_NIC_NAME)
    print('\nCreating Windows Virtual Machine')
    # Create Windows VM
    vm_parameters = create_vm_parameters(nic.id, VM_REFERENCE['windows'],W_VM_NAME)
    async_w_vm_creation = compute_client.virtual_machines.create_or_update(
        GROUP_NAME, W_VM_NAME, vm_parameters)
    async_w_vm_creation.wait()
    # Start the VM
    print('\nStart Windows Virtual Machine')
    async_w_vm_start = compute_client.virtual_machines.start(GROUP_NAME, W_VM_NAME)
    async_w_vm_start.wait()
    return

def create_vnet(network_client):
    print('\nCreate Vnet')
    async_vnet_creation = network_client.virtual_networks.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        {
            'location': LOCATION,
            'address_space': {
                'address_prefixes': ['10.0.0.0/17']
            }
        }
    )
    async_vnet_creation.wait()
    return

def create_subnet(network_client):
    print('\nCreate Subnet')
    async_subnet_creation = network_client.subnets.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        SUBNET_NAME,
        {'address_prefix': '10.0.0.0/24'}
    )
    return async_subnet_creation.result()

def create_nic(network_client,NIC_NAME):
    """Create a Network Interface for a VM.
    """
    subnet_info = network_client.subnets.get(
        GROUP_NAME,
        VNET_NAME,
        SUBNET_NAME
    )

    # Create NIC
    print('\nCreate NIC')
    async_nic_creation = network_client.network_interfaces.create_or_update(
        GROUP_NAME,
        NIC_NAME,
        {
            'location': LOCATION,
            'ip_configurations': [{
                'name': IP_CONFIG_NAME,
                'subnet': {
                    'id': subnet_info.id
                }
            }]
        }
    )
    return async_nic_creation.result()

def create_vm_parameters(nic_id, vm_reference,VM_NAME):
    """Create the VM parameters structure.
    """
    return {
        'location': LOCATION,
        'os_profile': {
            'computer_name': VM_NAME,
            'admin_username': USERNAME,
            'admin_password': PASSWORD
        },
        'hardware_profile': {
            'vm_size': 'Standard_DS1'
        },
        'storage_profile': {
            'image_reference': {
                'publisher': vm_reference['publisher'],
                'offer': vm_reference['offer'],
                'sku': vm_reference['sku'],
                'version': vm_reference['version']
            }
        },
        'network_profile': {
            'network_interfaces': [{
                'id': nic_id,
            }]
        }
    }

if __name__ == '__main__':
    run()