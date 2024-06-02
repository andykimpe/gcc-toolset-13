%global __python /usr/bin/python3

%global scl_name_base    gcc-toolset
%global scl_name_version 13
%global scl              %{scl_name_base}-%{scl_name_version}
%global scl_name %scl
%global macrosdir        %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_root_sysconfdir}/rpm; echo $d)
%global install_scl      1
%if 0%{?fedora} >= 26 || 0%{?rhel} >= 8
%global rh_layout        1
%endif

%if 0%{?fedora} >= 20 && 0%{?fedora} < 27
# Requires scl-utils v2 for SCL integration, dropeed in F29
%global with_modules     1
%else
# Works with file installed in /usr/share/Modules/modulefiles/
%global with_modules     0
%endif

%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary: Package that installs %scl
Name: %scl_name
Version: 13.0
Release: 3%{?dist}
License: GPLv2+
Group: Applications/File
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source0: https://github.com/andykimpe/gcc-toolset-13/raw/el9/SOURCES/README
Source1: https://github.com/andykimpe/gcc-toolset-13/raw/el9/SOURCES/sudo.sh
Source2: https://github.com/andykimpe/gcc-toolset-13/raw/el9/SOURCES/gts-annobin-plugin-select.sh
Source3: https://github.com/andykimpe/gcc-toolset-13/raw/el9/SOURCES/macros-build

BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: scl-utils-build
BuildRequires: help2man
# Temporary work-around
BuildRequires: iso-codes
BuildRequires: environment-modules

Requires: %{scl_prefix}runtime
Requires: %{scl_prefix}gcc %{scl_prefix}gcc-c++ %{scl_prefix}gcc-gfortran
Requires: %{scl_prefix}binutils
Requires: %{scl_prefix}gdb
Requires: %{scl_prefix}dwz
Requires: %{scl_prefix}annobin-plugin-gcc
Obsoletes: %{name} < %{version}-%{release}
Obsoletes: %{scl_prefix}dockerfiles < %{version}-%{release}

%if 0%{?rhel} >= 8
BuildRequires: python3-devel
%endif

%global rrcdir %{_scl_root}/usr/lib/rpm/redhat

%description
This is the main package for %scl Software Collection.

%package runtime
Summary: Package that handles %scl Software Collection.
Group: Applications/File
Requires:  scl-utils
Requires:  environment-modules
Requires(post): /usr/sbin/semanage
Requires(post): /usr/sbin/selinuxenabled
Provides:  %{?scl_name}-runtime(%{scl_vendor})
Provides:  %{?scl_name}-runtime(%{scl_vendor})%{?_isa}

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary:   Package shipping basic build configuration
Group:     Development/Languages
Requires:  scl-utils-build
Requires:  %{?scl_name}-runtime%{?_isa} = %{version}-%{release}

%description build
Package shipping essential configuration macros
to build %scl Software Collection.


%package scldevel
Summary:   Package shipping development files for %scl
Group:     Development/Languages
Requires:  %{?scl_name}-runtime%{?_isa} = %{version}-%{release}

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %scl Software Collection.

%prep
%setup -c -T

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat <<'EOF' | tee README
%{expand:%(cat %{SOURCE0})}
EOF

%build

# Temporary helper script used by help2man.
cat <<\EOF | tee h2m_helper
#!/bin/sh
if [ "$1" = "--version" ]; then
  printf '%%s' "%{?scl_name} %{version} Software Collection"
else
  cat README
fi
EOF
chmod a+x h2m_helper
# Generate the man page.
help2man -N --section 7 ./h2m_helper -o %{?scl_name}.7

# Enable collection script
# ========================
cat <<EOF >enable
# General environment variables
export PATH=%{_bindir}\${PATH:+:\${PATH}}
export MANPATH=%{_mandir}\${MANPATH:+:\${MANPATH}}
export INFOPATH=%{_infodir}\${INFOPATH:+:\${INFOPATH}}
# ??? We probably don't need this anymore.
export PCP_DIR=%{_scl_root}
# bz847911 workaround:
# we need to evaluate rpm's installed run-time % { _libdir }, not rpmbuild time
# or else /etc/ld.so.conf.d files?
rpmlibdir=\$(rpm --eval "%%{_libdir}")
# bz1017604: On 64-bit hosts, we should include also the 32-bit library path.
# bz1873882: On 32-bit hosts, we should include also the 64-bit library path.
# bz2027377: Avoid unbound variables
if [ "\$rpmlibdir" != "\${rpmlibdir/lib64/}" ]; then
  rpmlibdir32=":%{_scl_root}\${rpmlibdir/lib64/lib}"
  rpmlibdir64=
else
  rpmlibdir64=":%{_scl_root}\${rpmlibdir/lib/lib64}"
  rpmlibdir32=
fi
# Prepend the usual /opt/.../usr/lib{64,}.
export LD_LIBRARY_PATH=%{_scl_root}\$rpmlibdir\$rpmlibdir64\$rpmlibdir32\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export PKG_CONFIG_PATH=%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}
EOF

# generate rpm macros file for depended collections
cat << EOF | tee scldev
%%scl_%{scl_name_base}         %{scl}
%%scl_prefix_%{scl_name_base}  %{scl_prefix}
EOF

# Sudo script
# ===========
cat <<'EOF' > sudo
%{expand:%(cat %{SOURCE1})}
EOF

%install
(%{scl_install})

# We no longer need this, and it would result in an "unpackaged but
# installed" error.
rm -rf %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config

# This allows users to build packages using DTS/GTS.
cat >> %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-enable << EOF
%%enable_devtoolset13 %%global ___build_pre %%{___build_pre}; source scl_source enable %{scl} || :
EOF

mkdir -p %{buildroot}%{_scl_root}/etc/alternatives %{buildroot}%{_scl_root}/var/lib/alternatives

install -d -m 755 %{buildroot}%{_scl_scripts}
install -p -m 755 enable %{buildroot}%{_scl_scripts}/

install -d -m 755 %{buildroot}%{_scl_scripts}
install -p -m 755 sudo %{buildroot}%{_bindir}/

# Other directories that should be owned by the runtime
install -d -m 755 %{buildroot}%{_datadir}/appdata
# Otherwise unowned perl directories
install -d -m 755 %{buildroot}%{_libdir}/perl5
install -d -m 755 %{buildroot}%{_libdir}/perl5/vendor_perl
install -d -m 755 %{buildroot}%{_libdir}/perl5/vendor_perl/auto

# Install generated man page.
install -d -m 755 %{buildroot}%{_mandir}/man7
install -p -m 644 %{?scl_name}.7 %{buildroot}%{_mandir}/man7/

# Install the plugin selector trigger script.
mkdir -p %{buildroot}%{rrcdir}
install -p -m 755 %{SOURCE2} %{buildroot}%{rrcdir}/

# This trigger is used to decide which version of the annobin plugin for gcc
# should be used.  See comments in the script for full details.

%triggerin runtime -- %{scl_prefix}annobin-plugin-gcc %{scl_prefix}gcc-plugin-annobin
%{rrcdir}/gts-annobin-plugin-select.sh %{_scl_root}
%end

# We also trigger when annobin is uninstalled.  This allows us to switch
# over to the gcc generated version of the plugin.  It does not matter if
# gcc is uninstalled, since if that happens the plugin cannot be used.

%triggerpostun runtime -- %{scl_prefix}annobin-plugin-gcc
%{rrcdir}/gts-annobin-plugin-select.sh %{_scl_root}
%end
# Add the scl_package_override macro
#sed -e 's/@SCL@/%{scl}/g;s:@PREFIX@:/opt/%{scl_vendor}:;s/@VENDOR@/%{scl_vendor}/' %{SOURCE3} \
#  | tee -a %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config
sed -e 's/@SCL@/%{scl}/g;s:@PREFIX@:/opt/%{scl_vendor}:;s/@VENDOR@/%{scl_vendor}/' %{SOURCE3}
cat %{SOURCE3} > %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config

# Move in correct location, if needed
if [ "%{_root_sysconfdir}/rpm" != "%{macrosdir}" ]; then
  mv  %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl}-config \
      %{buildroot}%{macrosdir}/macros.%{scl}-config
fi

%post runtime
# Simple copy of context from system root to SCL root.
semanage fcontext -a -e /                      %{?_scl_root}     &>/dev/null || :
%if 0%{?fedora} >= 26 || 0%{?rhel} >= 8
semanage fcontext -a -e %{_root_sysconfdir}    %{_sysconfdir}    &>/dev/null || :
semanage fcontext -a -e %{_root_localstatedir} %{_localstatedir} &>/dev/null || :
%endif
selinuxenabled && load_policy || :
restorecon -R %{?_scl_root}     &>/dev/null || :
%if 0%{?fedora} >= 26 || 0%{?rhel} >= 8
restorecon -R %{_sysconfdir}    &>/dev/null || :
restorecon -R %{_localstatedir} &>/dev/null || :
%endif

%preun runtime
[ $1 = 0 ] && rm -f %{_sysconfdir}/selinux-equiv.created || :

%postun runtime
if [ $1 = 0 ]; then
  /usr/sbin/semanage fcontext -d %{_scl_root}
  [ -d %{_scl_root} ] && restorecon -R %{_scl_root} || :
fi

%files
%doc README
%{_mandir}/man7/%{?scl_name}.*

%if 0%{?fedora} < 19 && 0%{?rhel} < 7
%files runtime
%else
%files runtime -f filesystem
%endif
%defattr(-,root,root)
%attr(0755,-,-) %{rrcdir}/gts-annobin-plugin-select.sh
%scl_files
%{_root_sysconfdir}/rpm/macros.%{scl}-enable
%attr(0644,root,root) %verify(not md5 size mtime) %ghost %config(missingok,noreplace) %{_sysconfdir}/selinux-equiv.created
%dir %{_scl_root}/etc/alternatives
%dir %{_datadir}/appdata

%files build
%defattr(-,root,root)
%{macrosdir}/macros.%{scl}-config


%changelog
* Thu Aug  3 2023 Marek Polacek <polacek@redhat.com> - 13.0-2
- require GTS 13 packages (#2217519)

* Thu May  4 2023 Marek Polacek <polacek@redhat.com> - 13.0-1
- don't require other GTS 13 packages yet

* Fri Apr 21 2023 Marek Polacek <polacek@redhat.com> - 13.0-0
- update to GTS 13 (#2188491)
- drop gcc-toolset-13-build

* Mon Dec 05 2022 Nick Clifton  <nickc@redhat.com> - 12.0-6
- Use triggers to select which version of the annobin plugin should be used.  (#211175)

* Wed Jun 29 2022 Marek Polacek <polacek@redhat.com> - 12.0-5
- require -annobin-plugin-gcc (#2102356)

* Mon Jun 13 2022 Marek Polacek <polacek@redhat.com> - 12.0-4
- NVR bump and rebuild

* Fri May 27 2022 Marek Polacek <polacek@redhat.com> - 12.0-3
- use rpm/macros.%{scl}-enable for %enable_devtoolset12 and put it in
  the -runtime subpackage (#2009528)

* Fri May 27 2022 Marek Polacek <polacek@redhat.com> - 12.0-2
- cut down the required packages, remove -toolchain and -perftools

* Mon May 16 2022 Martin Cermak <mcermak@redhat.com> - 12.0-1
- NVR bump and rebuild, introduce CI gating setup

* Tue May 10 2022 Marek Polacek <polacek@redhat.com> - 12.0-0
- new package (#2077277)
