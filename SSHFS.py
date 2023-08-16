import os, json, time, hashlib
import sublime, sublime_plugin
from os import system

class BaseSshFsCommand(sublime_plugin.WindowCommand):
    MSG_FAILED_MOUNT    = "Failed to mount server: "
    MSG_FAILED_UMOUNT   = "Failed to umount server: "
    MSG_SSHFS_NOT_ISSET = "Command sshfs not found in your system!\n"\
                          "Please use command for Ubuntu/Debian: apt-get install sshfs\n"\
                          "Or other command for your distribution"
    NOT_FOUND_MOUNT_SERVERS = "Mounted servers not found, its OK"

    def run(self):
        if not self.sshfs_isset():
            sublime.error_message(self.MSG_SSHFS_NOT_ISSET)
            return False

        self.PLUGIN_NAME     = "SSHFS"
        self.PLUGIN_PATH     = sublime.packages_path() + '/' + self.PLUGIN_NAME
        self.MOUNT_DIR       = self.PLUGIN_PATH + "/mnt/"
        self.SERVERS_CONFIG  = self.PLUGIN_PATH + '/Servers.sublime-settings'
        self.DEBUG           = True

        self.check_mount_dir()
        self.servers = self.servers_load()

    def logger(self, message):
        if self.DEBUG:
            print("[SSHFS] %s" % message)
        else:
            return False

    # check sshfs bin
    def sshfs_isset(self):
        result = system('sshfs -V')
        return not result

    # check and create if not exists mount dir
    def check_mount_dir(self):
        if not os.path.exists(self.MOUNT_DIR):
            os.makedirs(self.MOUNT_DIR)

    # load servers list from config
    def servers_load(self):
        with open(self.SERVERS_CONFIG) as data:
            return json.load(data)

    # return path to mount dir for server
    def get_mount_dir(self, server):
        dir_name = "%s_%s_%s" % (server['name'], server['user'], server['host'])
        return self.MOUNT_DIR + dir_name + "/"

    # mount sshfs and open dir with files
    def sshfs_mount(self, server):
        mount_directory = self.get_mount_dir(server)

        if not os.path.exists(mount_directory):
            os.makedirs(mount_directory)

        command = "echo '%s' | sshfs -p %s -o password_stdin %s@%s:%s '%s'" % (
            server.get('port',22),
            server['password'], 
            server['user'], 
            server['host'], 
            server['directory'], 
            mount_directory
        )

        result = system(command)

        self.logger(command)

        if not result:
            system("subl '%s'" % mount_directory)
        else:
            sublime.error_message(self.MSG_FAILED_MOUNT + server['name'])

        return not result

    # check data and run sshfs_mount function
    def connect_to_server(self, id):
        if id < 0:
            return False

        servers = self.servers_load()
        return self.sshfs_mount(servers[id])

    # return servers list
    def servers_list(self):
        items = []
        servers = self.servers_load()
        for server in servers:
            items.append("%s: %s@%s" % (server['name'], server['user'], server['host']))

        return items

    def servers_mount_list(self):
        items = []
        servers = self.servers_load()

        for server in servers:
            if os.path.exists(self.get_mount_dir(server)):
                items.append("* %s: %s@%s" % (server['name'], server['user'], server['host']))
            else:
                items.append("%s: %s@%s" % (server['name'], server['user'], server['host']))


        return items

    # check data and run sshfs_umount function
    def disconnect_server(self, id):
        if id < 0:
            return False

        servers = self.servers_load()
        return self.sshfs_umount(servers[id])

    # umount sshfs directory
    def sshfs_umount(self, server):   
        mount_directory = self.get_mount_dir(server)
        command = "fusermount -uz '%s'" % mount_directory
        result = system(command)

        self.logger(command)

        if result:
            sublime.error_message(self.MSG_FAILED_UMOUNT + server['name'])
        else:
            os.rmdir(mount_directory)

        return not result

# sublime command
# open servers list for mount
class SshFsMountCommand(BaseSshFsCommand):
    def run(self):
        super(SshFsMountCommand, self).run()
        self.window.show_quick_panel(self.servers_list(), self.connect_to_server)

# sublime command
# open servers list for umount
class SshFsUmountCommand(BaseSshFsCommand):
    def run(self):
        super(SshFsUmountCommand, self).run()
        self.window.show_quick_panel(self.servers_mount_list(), self.disconnect_server)    

# sublime command
# open json file with servers configuration
class SshFsEditServersCommand(BaseSshFsCommand):
    def run(self):
        super(SshFsEditServersCommand, self).run()
        self.window.open_file(self.SERVERS_CONFIG)
