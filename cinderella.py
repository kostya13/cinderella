#
# Konstantin Ilyashenko <Konstantin_Ilyashenko@epam.com>
#
import cinderclient
import cinderclient.v1.client
import novaclient
import novaclient.v1_1.client
import paramiko


"""
Helper for common operations with Cinder volume.
"""


def check_name(fun):
    """Decorator for check valid volume identifier"""
    def wrapped(self, name):
        """Wrapper check valid name

        :param name: Volume identifier.
                     May be volume name, or volume id. name must be a string.
        """
        if not isinstance(name, str):
            raise ValueError("Incorrect type of name")
        if not name:
            raise ValueError("Empty name")
        return fun(self, name)
    return wrapped


class VolumeHelper:
    """Helper for some operations with Cinder volume."""

    def __init__(self, user, password, tenant, auth_url):
        """Init helper

            Authentication parameters.
            :param user: user name
            :param password: user password
            :param tenant: project tenant
            :param auth_url: url for authentication.
                             For example: "http://127.0.0.1:5000/v2.0/"
        """
        self.cinder_client = cinderclient.v1.client.Client(user, password, tenant, auth_url)
        self.nova_client = novaclient.v1_1.client.Client(user, password, tenant, auth_url)

    @check_name
    def _find_volume(self, name):
        """Find volume by name or id

           :param name: volume display_name or id
        """
        try:
            return self.cinder_client.volumes.get(name)
        except cinderclient.exceptions.NotFound:
            pass  # skip check by id

        try:
            return self.cinder_client.volumes.list(search_opts={"display_name": name})[0]
        except IndexError:
            raise ValueError("Can't find volume")

    @check_name
    def _find_server(self, name):
        """Find server by name or id

           :param name: server name or id
        """
        try:
            return self.nova_client.servers.get(name)
        except novaclient.exceptions.NotFound:
            pass  # skip check by id

        try:
            return self.nova_client.servers.list(search_opts={"name": "^{}$".format(name)})[0]
        except IndexError:
            raise ValueError("Can't find server")

    def _get_attached_host_parameters(self, volume_id):
        """Retrieve parameters of attached host, for current volume

           :param volume_id: id for volume
        """
        try:
            vol = self.cinder_client.volumes.get(volume_id)
            return vol._info["attachments"][0]
        except IndexError:
            raise ValueError("Volume not attached")

    def create(self, size, name=None, **kwargs):
        """Create volume

           :param size: volume size in Gb
           :param name: voilume name
           :param **kwargs: rest parameters for VolumeManager.create()
           :return: volume id
        """
        volume = self.cinder_client.volumes.create(display_name=name, size=size, **kwargs)
        return volume.id

    def lookup(self, name):
        """Find volume by name or id

           :param name: volume display_name or id
           :return: volume id
        """
        volume = self._find_volume(name)
        return volume.id

    def delete(self, name):
        """Delete volume

           :param name: volume display_name or id
        """
        volume = self._find_volume(name)
        self.cinder_client.volumes.delete(volume)

    def attach(self, volume, host, mount_point):
        """Attach volume to host

           :param volume: volume display_name or id
           :param host: server name or id
           :param mount_point: point where mount volume
        """
        vm = self._find_server(host)
        vol = self._find_volume(volume)
        # attach volume via nova to prevent the bug:
        # http://www.florentflament.com/blog/openstack-volume-in-use-although-vm-doesnt-exist.html
        self.nova_client.volumes.create_server_volume(vm.id, vol.id, mount_point)

    def detach(self, volume):
        """Detach volume from host

           :param volume: volume display_name or id
        """
        vol = self._find_volume(volume)
        try:
            server_id = self._get_attached_host_parameters(vol.id)["server_id"]
            self.nova_client.volumes.delete_server_volume(server_id, vol.id)
        except IndexError:
            raise Exception("Can't get server id")

    def format_volume(self, volume, host_user, host_password, command="/usr/sbin/mkfs.ext3"):
        """Format attached volume on VM

            :param volume: volume to format. Volume mut be alredy attached.
            :param host_user: ssh login user for the host.
                              User must have root privileges to run command with sudo.
            :param host_password: user password for the host.
            :param command: format command. Must be  full path.
        """
        def get_ip(net):
            """Helper functions to get host IP address from server networks dictonary

                :param net: dictonary with networks parameters
            """
            try:
                return net.values()[0][0]
            except IndexError:
                raise ValueError("Can't get IP address")

        try:
            vol = self._find_volume(volume)
            parameters = self._get_attached_host_parameters(vol.id)
            server_id = parameters["server_id"]
            server = self.nova_client.servers.get(server_id)
            ip = get_ip(server.networks)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=ip, username=host_user, password=host_password)
            device = parameters["device"]
            stdin, stdout, stderr = client.exec_command('sudo {}  {}'.format(command, device))
            stdin.write('{}\n'.format(host_password))
            stdin.flush()
            error = stderr.read()
            if "command not found" in error:  # very simple error check
                raise Exception(error)
        except ValueError:
            raise Exception("Can't format volume")
