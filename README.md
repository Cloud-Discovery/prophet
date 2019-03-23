# About

* Prophet is a collection tool for investigate source and target in user Windows or Linux environment

# Dependency

* yum install -y sshpass

* MySQL

# Docker Build

* TODO

# How to run?

usage: prophet-cli [-?] {linux_host,vmware_host,shell,runserver} ...

positional arguments:
  {linux_host,vmware_host,shell,runserver}
    linux_host          Linux host management
    vmware_host         VMware host management
    shell               Runs a Python shell inside Flask application context.
    runserver           Runs the Flask development server i.e. app.run()

optional arguments:
  -?, --help            show this help message and exit
