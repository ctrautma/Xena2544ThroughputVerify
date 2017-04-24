# Xena2544ThroughputVerify
Instructions:
1.  For linux Install Mono ->
    rpm --import "http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF"
    yum-config-manager --add-repo http://download.mono-project.com/repo/centos/
    yum -y install mono-complete
2. If python 3 not installed, install python 3. For RHEL instructions are below->
   Add this repo as python33.repo for your repo file locations. /etc/yum.repos.d
    [rhscl-python33-el7]
    name=Copr repo for python33-el7 owned by rhscl
    baseurl=https://copr-be.cloud.fedoraproject.org/results/rhscl/python33-el7/epel-7-$basearch/
    type=rpm-md
    skip_if_unavailable=True
    gpgcheck=1
    gpgkey=https://copr-be.cloud.fedoraproject.org/results/rhscl/python33-el7/pubkey.gpg
    repo_gpgcheck=0
    enabled=1
    enabled_metadata=1

    # install python33 package
    yum -y install python33 python33-python-tkinter
    # cleanup python 33 repo file
    rm -f /etc/yum.repos.d/python33.repo

3. Enable python33 -> scl enable python33 bash

4. Make sure Xena2544.exe is present in the current folder

5. Copy your x2544 config file to the script folder

6. Arguments to run this script
    -f <path to config file> saved from Xena2544.exe GUI with your config.
    -s enable smart search, if verify fails will resume the search at the half
       way point between the last verify attempt and the minimum search value.
       Otherwise it will just resume at the last verify attempt value minus
       the value threshhold.
    -l <verify length in seconds> Default of 2 hours.
    -r <retry attempts> Maximum number of verify attempts for giving up
    -d Enable debug mode
    -p Output PDF file. By default output of PDF report is disabled. Will cause
       a crash on linux usually as a pdf renderer is not installed.
    -w Enable windows mode. By default it will use the mono package to run the
       exe file. If running on windows this is not necessary.
    -t <search trial duration in seconds> Modify original config to use the
       duration specified.

7. Sample execution ->
   Runs a 60 second trial with a 600 second verify using the myconfig.x2544
   configuration file.
   python XenaVerify.py -f myconfig.x2544 -s -l 600 -t 60

Improvements to be done
- Add debug logging
- Add more customized options for modifying the running config
- Add python 2.7 support
