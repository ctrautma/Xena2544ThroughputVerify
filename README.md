# Xena2544ThroughputVerify
Instructions:

1.  For linux Install Mono ->

    rpm --import "http://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF"

    yum-config-manager --add-repo http://download.mono-project.com/repo/centos/

    yum -y install mono-complete-5.8.0.127-0.xamarin.3.epel7.x86_64

2. If python 3 not installed, install python 3. For RHEL instructions are below->

     cat <<'EOT' >> /etc/yum.repos.d/python34.repo

     [centos-sclo-rh]

     name=CentOS-7 - SCLo rh

     baseurl=http://mirror.centos.org/centos/7/sclo/$basearch/rh/

     gpgcheck=0

     enabled=1

     gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-SIG-SCLo

     EOT

    # install python34 scl package

    yum -y install rh-python34 rh-python34-python-tkinter

    # cleanup python 34 repo file

    rm -f /etc/yum.repos.d/python34.repo

3. Enable python34 -> scl enable rh-python34 bash

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
