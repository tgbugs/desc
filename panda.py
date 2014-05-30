#so it looks like it is possible to stream stuff in using multifiles in pand3d
#obviously in the long run we will probably want our own optimized renderer
#but this is somehwere to start
#install is a freeking mess

#must install with --no-ode because there is some weird error with python3.4
#not sure why... it works fine on athena


#utf-8 decoding problems somehwere... looks like it is in core.NodePath
#rebuild with symbols optimize=0

#FOUND YOU! tis in incremental/panda/src/pgraph/nodePath.cxx
    #actually in nodePath.h under get_tag

#the issue is in panda/src/pgraph/nodePath.c most likely?
#maybe it is actually in built/tmp/libp3graph_igate.cxx??

#specifically >> 
#if PY_MAJOR_VERSION >= 3
        return PyUnicode_FromStringAndSize(return_value.data(), (Py_ssize_t)return_value.length());
#<< specifically

#really it seems that pickle.dumps is the problem because it dumps to bytes not unicode
#and actually, it is more that there is a problem in interrogate... with py3 unicode c binding
#should be :
#PyObject* PyByteArray_FromStringAndSize(const char *string, Py_ssize_t len)
    #Create a new bytearray object from string and its length, len. On failure, NULL is returned.

#changing the following instances :
./direct/src/dcparser/dcPacker.cxx-949-#if PY_MAJOR_VERSION >= 3
./direct/src/dcparser/dcPacker.cxx:950:      object = PyUnicode_FromStringAndSize(str.data(), str.size());
--
./dtool/src/dtoolutil/filename.cxx-2012-    // This function expects UTF-8.
./dtool/src/dtoolutil/filename.cxx:2013:    PyObject *str = PyUnicode_FromStringAndSize(filename.data(), filename.size());
--
./dtool/src/dtoolutil/globPattern.cxx-138-    // This function expects UTF-8.
./dtool/src/dtoolutil/globPattern.cxx:139:    PyObject *str = PyUnicode_FromStringAndSize(filename.data(), filename.size());
--
./dtool/src/interrogate/interfaceMakerPythonNative.cxx-1790-      out << "#if PY_MAJOR_VERSION >= 3\n";
./dtool/src/interrogate/interfaceMakerPythonNative.cxx:1791:      out << "  return PyUnicode_FromStringAndSize(ss.data(), ss.length());\n";
--
./dtool/src/interrogate/interfaceMakerPythonNative.cxx-1819-      out << "#if PY_MAJOR_VERSION >= 3\n";
./dtool/src/interrogate/interfaceMakerPythonNative.cxx:1820:      out << "  return PyUnicode_FromStringAndSize(ss.data(), ss.length());\n";
--
./dtool/src/interrogate/interfaceMakerPythonNative.cxx-3336-      indent(out, indent_level+2) << assign_stmt
./dtool/src/interrogate/interfaceMakerPythonNative.cxx:3337:        << "PyUnicode_FromStringAndSize("
--
./dtool/src/interrogate/interfaceMakerPythonNative.cxx-3349-      indent(out, indent_level) << assign_stmt
./dtool/src/interrogate/interfaceMakerPythonNative.cxx:3350:        << "PyUnicode_FromStringAndSize("
--
./dtool/src/interrogate/interfaceMakerPythonObj.cxx-587-      indent(out, indent_level)
./dtool/src/interrogate/interfaceMakerPythonObj.cxx:588:        << "return PyUnicode_FromStringAndSize("
--
./dtool/src/interrogate/interfaceMakerPythonSimple.cxx-488-      indent(out, indent_level)
./dtool/src/interrogate/interfaceMakerPythonSimple.cxx:489:        << "return PyUnicode_FromStringAndSize("
--
./dtool/src/pystub/pystub.cxx-146-  EXPCL_PYSTUB int PyUnicode_FromString(...);
./dtool/src/pystub/pystub.cxx:147:  EXPCL_PYSTUB int PyUnicode_FromStringAndSize(...);
--
./dtool/src/pystub/pystub.cxx-310-int PyUnicode_FromString(...) { return 0; }
./dtool/src/pystub/pystub.cxx:311:int PyUnicode_FromStringAndSize(...) { return 0; }
./panda/src/pgraph/pandaNode_ext.cxx-222-#if PY_MAJOR_VERSION >= 3
./panda/src/pgraph/pandaNode_ext.cxx:223:    PyObject *str = PyUnicode_FromStringAndSize(tag_name.data(), tag_name.size());
--
./panda/src/pgraph/pandaNode_ext.cxx-247-#if PY_MAJOR_VERSION >= 3
./panda/src/pgraph/pandaNode_ext.cxx:248:    PyObject *str = PyUnicode_FromStringAndSize(tag_name.data(), tag_name.size());

#further investigation seems to implicate pack_return_value?


#how to automatically search for models in ~/.local/share/panda3d/models????

"""
#dependencies: see: https://www.panda3d.org/manual/index.php/Third-party_dependencies_and_license_info
    python
    nvidia-cg-toolkit
    eigen

must ./configure --enable-shared when building python
in order to actually get panda3d to find the bloody Python.h and libpython3.4 we need to???
    modify makepandacore.py (there is probably somewhere correct to do this)
    ~ MUST be the full path written out eg /home/tgillesp
    add ~/.local/include to INCDIRECTORIES 2172
    add ~/.local/lib to LIBDIRECTORIES 2173
    will need to add the nvidia cg toolkit as well if want to run tuts... for some reason this is broken...
    have to manually ln -s Cg into includes... stupid that you have to do it manually instead of being
    able to just tell the build where to look >_< it seemed to work for python at salk...
    just kidding, I probably need to add th stuf to LD_LIBRARY_PATH that's probably a smarter idea...
    C_INCLUDE_PATH
    CPLUS_INCLUDE_PATH
    LD_LIBRARY_PATH #but, for now it works for nvidia and I'm not going to worry about it
    #turns out the NVIDIACG problem is that CGGL is ALSO required but listed nowhere...

#to clean previous install
rm -r ~/.local/lib64/python3.x/site-packages/panda3d
rm -r ~/.local/lib64/panda3d
rm -r ~/.local/share/panda3d

#NOTE: --no-ode will cause segfaults on athena >_< ?? FALSE
python makepanda/makepanda.py --everything --threads 8 --optimize 3 --verbose --no-od
python makepanda/installpanda.py --destdir=/home/tgillesp/.local/ --prefix=/

#then you meed to
mv ~/.local/usr/lib64/python3.3/site-packages/panda3d ~/.local/lib64/python3.3/site-packages/panda3d 

The right way to do this is as follows:
1) run makepanda/makepanda.py with the version of python you want panda3d to use
2) run python makepanda/installpanda.py --destdir=/home/user/.local/ --prefix=/
3) add /home/user/.local/lib64/panda3d to LD_LIBRARY_PATH
un needed
#export PYTHONPATH=$PYTHONPATH:~/.local/share/panda3d/direct:~/.local/share/panda3d/pandac
"""

