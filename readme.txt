"Cinderella" is Openstack python module for operation with Cinder volumes.
This module provide the following functionality:
- Create a volume
- Lookup a volume by its name
- Attach a volume to an existing VM
- Attach using server id or server name, volume ID or volume name.
- Detach a volume from VM
- Delete a volume
- Format a volume after attaching it to a VM

For creating this test I am searched Google for:
- How to install OpenStack
- OpenStack user guide
- Existing python modules for OpenStack

Read the documentation for openstack specific modules and command line utilities.  	
Such as python-cinderclient, python-novaclient. Read source code for those modules.

Investigate how to work with openstack from command line and Web gui.

Found the bug in attach function. Solution founded in: http://www.florentflament.com/blog/openstack-volume-in-use-although-vm-doesnt-exist.html

I am testing code on my small Openstack installation under Ubuntu 14.04
