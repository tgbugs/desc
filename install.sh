PYTHON=python3.5
TEMP_DIR=/tmp/panda_magic/
INSTALL_DIR=/home/tom/.local/
mkdir $TEMP_DIR
cd ~/git/panda3d
$PYTHON makepanda/makepanda.py --everything --threads 8 --optimize 3 --verbose --no-ode --no-nvidiacg --no-eigen
$PYTHON makepanda/installpanda.py --prefix=/ --destdir=$TEMP_DIR
cd $TEMP_DIR
mv usr/lib64 .  # WARNING only works for an empty directory
rmdir usr
mv lib/panda3d lib64/ 
rmdir lib
sed -i "s|^/|${INSTALL_DIR}|" lib64/${PYTHON}/site-packages/panda3d.pth
# install something in env.d for LD_LIBRARY_PATH=${INSTALL_PATH}/lib64/panda3d ??

cp -a . $INSTALL_DIR

#cd $OLDPWD
#rm -r TEMP_DIR

# TODO check that this actually needs to be added?
#echo 'export LD_LIBRARY_PATH=${INSTALL_DIR}lib64/panda3d:${LD_LINK_PATH}' >> ~/.bashrc

