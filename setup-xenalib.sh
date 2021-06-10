#!/bin/bash
wget https://github.com/fleitner/XenaPythonLib/archive/refs/heads/master.zip
unzip master.zip
mv XenaPythonLib-master/xenalib .
rm -r XenaPythonLib-master/ master.zip

