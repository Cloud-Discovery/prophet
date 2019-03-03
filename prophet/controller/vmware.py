import atexit

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

class VMware(object):

    def __init__(self,
                 host=None,
                 port=443,
                 username=None,
                 password=None,
                 disable_ssl_verification=True):
        try:
            if disable_ssl_verification:
                service_instance = connect.SmartConnectNoSSL(host=host,
                                                             user=username,
                                                             pwd=password,
                                                             port=int(port))
            else:
                service_instance = connect.SmartConnect(host=host,
                                                        user=username,
                                                        pwd=password,
                                                        port=int(port))

            atexit.register(connect.Disconnect, service_instance)

            content = service_instance.RetrieveContent()

            container = content.rootFolder  # starting point to look into
            viewType = [vim.VirtualMachine]  # object types to look for
            recursive = True  # whether we should look into it recursively
            containerView = content.viewManager.CreateContainerView(
                container, viewType, recursive)

            children = containerView.view
            for child in children:
                self.print_vm_info(child)

        except vmodl.MethodFault as error:
            print("Caught vmodl fault : " + error.msg)
            return -1

    def print_vm_info(self, virtual_machine):
        """
        Print information for a particular virtual machine or recurse into a
        folder with depth protection
        """
        summary = virtual_machine.summary
        print("Name       : ", summary.config.name)
        print("Template   : ", summary.config.template)
        print("Path       : ", summary.config.vmPathName)
        print("Guest      : ", summary.config.guestFullName)
        print("Instance UUID : ", summary.config.instanceUuid)
        print("Bios UUID     : ", summary.config.uuid)
        annotation = summary.config.annotation
        if annotation:
            print("Annotation : ", annotation)
        print("State      : ", summary.runtime.powerState)
        if summary.guest is not None:
            ip_address = summary.guest.ipAddress
            tools_version = summary.guest.toolsStatus
            if tools_version is not None:
                print("VMware-tools: ", tools_version)
            else:
                print("Vmware-tools: None")
            if ip_address:
                print("IP         : ", ip_address)
            else:
                print("IP         : None")
        if summary.runtime.question is not None:
            print("Question  : ", summary.runtime.question.text)
        print("")
