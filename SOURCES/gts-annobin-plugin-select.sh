#!/usr/bin/sh
# This is a script to switch the symlinks in a GTS gcc's plugin
# directory so that they select either the GTS-annobin provided
# plugin or the GTS-gcc provided plugin.

# Author: Nick Clifton  <nickc@redhat.com>
# Copyright (c) 2021-2022 Red Hat.
#
# This is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2, or (at your
# option) any later version.

# It is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Usage:
#   gts-annobin-plugin-select scl_root
#

# Set this variable to non-zero to enable the generation of debugging
# messages.
debug=0

if test "x$1" = "x" ;
then
    if [ $debug -eq 1 ]
    then
	echo "  gts-annobin-plugin-select: Must provide a root directory"
    fi
    exit 1
else
    scl_root=$1
fi

# This script is similar to the redhat-annobin-plugin-select.sh script which
# is part of the redhat-rpm-config package.  That scripts decides between two
# versions of the annobin plugin for the system compiler and stores it choice
# in a symlink in the /usr/lib/rpm/redhat directory.  The choice eventually
# resolves into the system gcc attempting to load either a plugin called
# annobin.so or a plugin called gcc-annobin.so.

# In a GTS environment the choice made by redhat-annobin-plugin-select.sh
# might not be appropriate (or even possible).  The choice cannot be changed
# because the system compilation environment must remain instact.  So instead
# the GTS versions of gcc and annobin install plugins called gts-annobin.so
# and gts-gcc-annobin.so (into the GTS gcc's plugin directory) and this script
# creates a pair of symlinks called annobin.so and gcc-annobin.so.  In this
# way the decision made by redhat-annobin-plugin-select.sh is overridden
# without affecting any system files.

# We cannot be sure that this script will run inside a GTS enabled shell,
# so we have to use absolute paths.
gts_gcc=$scl_root/usr/bin/gcc

if [ ! -x $gts_gcc ]
then
    if [ $debug -eq 1 ]
    then
	echo "  gts-annobin-plugin-select: Could not find gcc.  Expected: $gts_gcc"
    fi
    exit 0
fi

# This is where the annobin package stores the information on the version
# of gcc that built the annobin plugin.
aver=`$gts_gcc --print-file-name=plugin`/annobin-plugin-version-info

# This is where the gcc package stores its version information.
gver=`$gts_gcc --print-file-name=rpmver`

aplugin=`$gts_gcc --print-file-name=plugin`/gts-annobin.so.0.0.0
gplugin=`$gts_gcc --print-file-name=plugin`/gts-gcc-annobin.so.0.0.0

install_annobin_version=0
install_gcc_version=0

if [ -f $aplugin ]
then
    if [ -f $gplugin ]
    then
	if [ $debug -eq 1 ]
	then
	    echo "  gts-annobin-plugin-select: Both plugins exist, checking version information"
	fi

	if [ -f $gver ]
	then
	    if [ -f $aver ]
	    then
		if [ $debug -eq 1 ]
		then
		    echo "  gts-annobin-plugin-select: Both plugin version files exist - comparing..."
		fi

		# Get the first line from the version info files.  This is just in
		# case there are extra lines in the files.
		avers=`head --lines=1 $aver`
		gvers=`head --lines=1 $gver`

		if [ $debug -eq 1 ]
		then
		    echo "  gts-annobin-plugin-select: Annobin plugin built by gcc $avers"
		    echo "  gts-annobin-plugin-select: GCC     plugin built by gcc $gvers"
		fi

		# If both plugins were built by the same version of gcc then select
		# the one from the annobin package (in case it is built from newer
		# sources).  If the plugin builder versions differ, select the gcc
		# built version instead.  This assumes that the gcc built version
		# always matches the installed gcc, which should be true.
		if [ $avers = $gvers ]
		then
		    if [ $debug -eq 1 ]
		    then
			echo "  gts-annobin-plugin-select: Both plugins built by the same compiler - using annobin-built plugin"
		    fi
		    install_annobin_version=1
		else
		    if [ $debug -eq 1 ]
		    then
			echo "  gts-annobin-plugin-select: Versions differ - using gcc-built plugin"
		    fi
		    install_gcc_version=1
		fi
	    else
		if [ $debug -eq 1 ]
		then
		    echo "  gts-annobin-plugin-select: Annobin version file does not exist, using gcc-built plugin"
		fi
		install_gcc_version=1
	    fi
	else
	    if [ -f $aver ]
	    then
		# FIXME: This is suspicious.  If the installed GCC does not supports plugins
		# then enabling the annobin plugin will not work.
		if [ $debug -eq 1 ]
		then
		    echo "  gts-annobin-plugin-select: GCC plugin version file does not exist, using annobin-built plugin"
		fi
		install_annobin_version=1
	    else
		if [ $debug -eq 1 ]
		then
		    echo "  gts-annobin-plugin-select: Neither version file exists - playing safe and using gcc-built plugin"
		    echo "  gts-annobin-plugin-select: Note: expected to find $aver and/or $gver"
		fi
		install_gcc_version=1
	    fi
	fi
    else
	if [ $debug -eq 1 ]
	then
	    echo "  gts-annobin-plugin-select: Only the annobin plugin exists - using that"
	fi
	install_annobin_version=1
    fi
else
    if [ -f $gplugin ]
    then
	if [ $debug -eq 1 ]
	then
	    echo "  gts-annobin-plugin-select: Only the gcc plugin exists - using that"
	fi
	install_gcc_version=1
    else
	aplugin=`$gts_gcc --print-file-name=plugin`/annobin.so.0.0.0

	if [ -f $aplugin ]
	then
	    if [ $debug -eq 1 ]
	    then
		echo "  gts-annobin-plugin-select: Original annobin plugin exists - renaming"
		echo "  gts-annobin-plugin-select: Using renamed original annobin plugin"
	    fi
	    pushd `$gts_gcc --print-file-name=plugin` > /dev/null
	    mv annobin.so.0.0.0 gts-annobin.so.0.0.0
	    popd > /dev/null
	    install_annobin_version=1
	else
	    if [ $debug -eq 1 ]
	    then
		echo "  gts-annobin-plugin-select: Neither plugin exists - playing safe and not changing anything"
		echo "  gts-annobin-plugin-select: Note: expected to find $aplugin and/or $gplugin"
	    fi
	fi
    fi
fi

if [ $install_annobin_version -eq 1 ]
then
    if [ $debug -eq 1 ]
    then
	echo "  gts-annobin-plugin-select: Setting symlinks for the annobin version of the plugin"
    fi
    pushd `$gts_gcc --print-file-name=plugin` > /dev/null
    rm -f gcc-annobin.so.0.0.0 annobin.so.0.0.0 gcc-annobin.so annobin.so
    ln -s gts-annobin.so.0.0.0 annobin.so
    ln -s gts-annobin.so.0.0.0 gcc-annobin.so
    ln -s gts-annobin.so.0.0.0 annobin.so.0.0.0
    ln -s gts-annobin.so.0.0.0 gcc-annobin.so.0.0.0
    popd > /dev/null
    
else if [ $install_gcc_version -eq 1 ]
then
    if [ $debug -eq 1 ]
    then
	echo "  gts-annobin-plugin-select: Setting symlinks for the gcc version of the plugin"
    fi
    pushd `$gts_gcc --print-file-name=plugin` > /dev/null
    rm -f gcc-annobin.so.0.0.0     annobin.so.0.0.0 gcc-annobin.so annobin.so
    ln -s gts-gcc-annobin.so.0.0.0 annobin.so
    ln -s gts-gcc-annobin.so.0.0.0 gcc-annobin.so
    ln -s gts-gcc-annobin.so.0.0.0 annobin.so.0.0.0
    ln -s gts-gcc-annobin.so.0.0.0 gcc-annobin.so.0.0.0
    popd > /dev/null
else
    if [ $debug -eq 1 ]
    then
	echo "  gts-annobin-plugin-select: NOT CHANGING SYMLINKS"
    fi
fi
fi
