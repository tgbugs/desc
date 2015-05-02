PYTHON=python3.4
INSTALL_DIR=/tmp/panda_magic
mkdir $INSTALL_DIR
cd ~/git/panda3d
$PYTHON makepanda/makepanda.py --everything --threads 8 TODO
$PYTHON makepanda/installpanda.py --prefix=/ --destdir=$INSTALL_DIR
cd $INSTALL_DIR
mv usr/lib64 .
rmdir usr
mv lib/panda3d lib64/ 
rmdir lib
sed -i "s|^/|${PWD}|" lib64/python3.4/site-packages/panda3d.pth
# install something in env.d for LD_LIBRARY_PATH=${INSTALL_PATH}/lib64/panda3d ??
