#!/bin/bash
# download, unzip, cleanup XenaPythonLib
wget https://github.com/fleitner/XenaPythonLib/archive/refs/heads/master.zip
unzip master.zip
mv XenaPythonLib-master/xenalib .
rm -r XenaPythonLib-master/ master.zip

# install mono
rpm --import "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF"
su -c 'curl https://download.mono-project.com/repo/centos8-stable.repo | tee /etc/yum.repos.d/mono-centos8-stable.repo'
dnf update -y
dnf install mono-complete -y