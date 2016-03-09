import os, json
import sublime, sublime_plugin
from os import system

PLUGIN_NAME     = "SSHFS"
PLUGIN_PATH     = sublime.packages_path() + '/' + PLUGIN_NAME
MOUNT_DIR       = PLUGIN_PATH + "/mnt/"
SERVERS_CONFIG  = PLUGIN_PATH + '/Servers.sublime-settings'

# plugin loaded event
def plugin_loaded():
    if not os.path.exists(MOUNT_DIR):
        os.makedirs(MOUNT_DIR)

# return dict with servers and configs
def servers_load():
    with open(SERVERS_CONFIG) as data:
        return json.load(data)

# return path to mount dir for server
def get_mount_dir(server):
    return MOUNT_DIR + server['user'] + '@' + server['host'] + '_' + server['name']

# mount sshfs and open dir with files
def sshfs_mount(server):
    mount_directory = get_mount_dir(server)

    if not os.path.exists(mount_directory):
        os.makedirs(mount_directory)

    result = system(
        "echo '%s' | sshfs -o password_stdin %s@%s:%s '%s'" % (
            server['password'], 
            server['user'], 
            server['host'], 
            server['directory'], 
            mount_directory
        )
    )

    if not result:
        call(["subl", mount_directory])
    else:
        sublime.error_message('Failed to mount directory: ' + mount_directory)

    return not result

# umount sshfs directory
def sshfs_umount(server):   
    mount_directory = get_mount_dir(server)
    result = system("fusermount -u %s" % mount_directory)

    if result:
        sublime.error_message('Failed to umount directory: ' + mount_directory)

    return not result

# check data and run sshfs_mount function
def connect_to_server(id):
    if id < 0:
        return False

    servers = servers_load()
    print("Connect to server: " + servers[id]['name'])
    return sshfs_mount(servers[id])

# check data and run sshfs_umount function
def disconnect_server(id):
    if id < 0:
        return False

    servers = servers_load()
    return sshfs_umount(servers[id])

# sublime command
# open servers list for mount
class SshFsMountCommand(sublime_plugin.WindowCommand):
    def run(self):
        items = []
        servers = servers_load()
        for server in servers:
            items.append(server['name'] + ': ' + server['user'] + '@' + server['host'])

        self.window.show_quick_panel(items, connect_to_server)

# sublime command
# open servers list for umount
class SshFsUmountCommand(sublime_plugin.WindowCommand):
    def run(self):
        items = []
        servers = servers_load()
        for server in servers:
            items.append(server['name'] + ': ' + server['user'] + '@' + server['host'])

        self.window.show_quick_panel(items, disconnect_server)

# sublime command
# open json file with servers configuration
class SshFsEditServersCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.open_file(SERVERS_CONFIG)