#
# Konstantin Ilyashenko <Konstantin_Ilyashenko@epam.com>
#
from mock import patch
import cinderella
import mock
import time

"""
Tests for cinderella module
"""

user = "admin"
password = "password"
tenant = "admin"
auth_url = "http://127.0.0.1:5000/v2.0/"
volume_name = "test_volume"
volume_size = 1
instance = "demo-instance1"


def infrastructure_test():
    """Test module in OpenStack infrastructure"""
    
    helper = cinderella.VolumeHelper(user, password, tenant, auth_url)
    vol_id = helper.create(volume_size, volume_name)
    print "Volume created: ", vol_id
    time.sleep(3)
    vol_id_looked = helper.lookup(volume_name)
    assert(vol_id == vol_id_looked)
    helper.attach(volume_name, instance, "/dev/vdb")
    time.sleep(5)
    helper.format_volume(volume_name, "cirros", "cubswin:)")
    time.sleep(5)
    helper.detach(volume_name)
    time.sleep(5)
    helper.delete(volume_name)


@patch("novaclient.v1_1.client")
@patch("cinderclient.v1.client")
def mock_test(cinder, nova):
    """Test module with mocks"""
    
    test_id = "123"

    cinder.Client.return_value.volumes.get.return_value.id = test_id
    cinder.Client.return_value.volumes.create.return_value.id = test_id

    helper = cinderella.VolumeHelper(user, password, tenant, auth_url)

    assert(test_id == helper.create(volume_size, volume_name))
    assert(test_id == helper.lookup(volume_name))

    helper.attach(volume_name, instance, "/dev/vdb")
    assert(nova.Client.return_value.volumes.create_server_volume.called)

# format not checked on mocks

    helper.detach(volume_name)
    assert(nova.Client.return_value.volumes.delete_server_volume.called)

    helper.delete(volume_name)
    assert(cinder.Client.return_value.volumes.delete.called)

if __name__ == "__main__":
    print "Run tests"
    infrastructure_test()
    mock_test()
