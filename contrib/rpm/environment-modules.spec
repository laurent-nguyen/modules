%global macrosdir %(d=%{_rpmconfigdir}/macros.d; [ -d $d ] || d=%{_sysconfdir}/rpm; echo $d)

Name:           environment-modules
Version:        4.0.0
Release:        0.1.beta%{?dist}
Summary:        Provides dynamic modification of a user's environment

Group:          System Environment/Base
License:        GPLv2+
URL:            http://modules.sourceforge.net/
Source0:        http://downloads.sourceforge.net/modules/modules-%{version}-beta.tar.bz2
Source1:        createmodule.sh
Source2:        createmodule.py

BuildRequires:  tcl
BuildRequires:  dejagnu
BuildRequires:  perl
%if 0%{?fedora} || (0%{?rhel} && 0%{?rhel} > 6)
BuildRequires:  perl-podlators
%endif
%if 0%{?rhel} && 0%{?rhel} <= 6
BuildRequires:  net-tools
%else
BuildRequires:  hostname
%endif
# specific requirements to build compat version
BuildRequires:  tcl-devel, tclx-devel, libX11-devel
Requires:       tcl
Requires:       sed
%if 0%{?rhel} && 0%{?rhel} <= 6
Requires:       procps
Requires:       man
Requires:       net-tools
%else
Requires:       procps-ng
Requires:       man-db
Requires:       hostname
%endif
Requires(post): coreutils
Requires(post): %{_sbindir}/update-alternatives
Requires(postun): %{_sbindir}/update-alternatives
%if 0%{?fedora}
Provides:       environment(modules)
%else
Provides:       environment-modules
%endif

%description
The Environment Modules package provides for the dynamic modification of
a user's environment via modulefiles.

Each modulefile contains the information needed to configure the shell
for an application. Once the Modules package is initialized, the
environment can be modified on a per-module basis using the module
command which interprets modulefiles. Typically modulefiles instruct
the module command to alter or set shell environment variables such as
PATH, MANPATH, etc. modulefiles may be shared by many users on a system
and users may have their own collection to supplement or replace the
shared modulefiles.

Modules can be loaded and unloaded dynamically and atomically, in an
clean fashion. All popular shells are supported, including bash, ksh,
zsh, sh, csh, tcsh, as well as some scripting languages such as perl.

Modules are useful in managing different versions of applications.
Modules can also be bundled into metamodules that will load an entire
suite of different applications.

NOTE: You will need to get a new shell after installing this package to
have access to the module alias.

%package compat
Summary:        Environment Modules compatibility version
Requires:       environment-modules = %{version}-%{release}

%description compat
The Environment Modules package provides for the dynamic modification of
a user's environment via modulefiles.

This package provides Environment Modules compatibility version (3.2).


%prep
%setup -q -n modules-%{version}-beta


%build
# configure script for this software is not generated by autoconf
./configure --prefix=%{_datadir}/Modules \
            --mandir=%{_mandir} \
            --disable-doc-install \
            --enable-dotmodulespath \
            --with-modulepath=%{_datadir}/Modules/modulefiles:%{_sysconfdir}/modulefiles:%{_datadir}/modulefiles
make %{?_smp_mflags}


%install
make install DESTDIR=%{buildroot}

mkdir -p %{buildroot}%{_sysconfdir}/modulefiles
mkdir -p %{buildroot}%{_datadir}/modulefiles

mkdir -p %{buildroot}%{_sysconfdir}/profile.d
mkdir -p %{buildroot}%{_bindir}
%if 0%{?fedora}
# setup for alternatives on Fedora
touch %{buildroot}%{_sysconfdir}/profile.d/modules.{csh,sh}
touch %{buildroot}%{_bindir}/modulecmd
%else
# install profile links
ln -s %{_datadir}/Modules/init/profile.csh %{buildroot}%{_sysconfdir}/profile.d/modules.csh
ln -s %{_datadir}/Modules/init/profile.sh %{buildroot}%{_sysconfdir}/profile.d/modules.sh
# link to main command in bin for compatibility
ln -s %{_datadir}/Modules/libexec/modulecmd.tcl %{buildroot}%{_bindir}/modulecmd
%endif

# major utilities go to regular bin dir
mv %{buildroot}%{_datadir}/Modules/bin/envml %{buildroot}%{_bindir}/

# rename compat docs to find them in files section
mv compat/ChangeLog ChangeLog-compat
mv compat/NEWS NEWS-compat

cp -p %SOURCE1 %SOURCE2 %{buildroot}%{_datadir}/Modules/bin
%if 0%{?fedora} >= 22
sed -i -e 1s,/usr/bin/python,/usr/bin/python3, \
    %{buildroot}%{_datadir}/Modules/bin/createmodule.py
%endif

# Install the rpm config file
install -Dpm 644 contrib/rpm/macros.%{name} %{buildroot}/%{macrosdir}/macros.%{name}


%check
make test


%if 0%{?fedora}
%post
# Cleanup from pre-alternatives
[ ! -L %{_sysconfdir}/profile.d/modules.sh ] &&  rm -f %{_sysconfdir}/profile.d/modules.sh
[ ! -L %{_sysconfdir}/profile.d/modules.csh ] &&  rm -f %{_sysconfdir}/profile.d/modules.csh
[ ! -L %{buildroot}%{_bindir}/modulecmd ] &&  rm -f %{_bindir}/modulecmd

# Migration from version 3.x to 4
if [ "$(readlink /etc/alternatives/modules.sh)" = '%{_datadir}/Modules/init/modules.sh' ]; then
  %{_sbindir}/update-alternatives --remove modules.sh %{_datadir}/Modules/init/modules.sh
fi

%{_sbindir}/update-alternatives \
  --install %{_sysconfdir}/profile.d/modules.sh modules.sh %{_datadir}/Modules/init/profile.sh 40 \
  --slave %{_sysconfdir}/profile.d/modules.csh modules.csh %{_datadir}/Modules/init/profile.csh \
  --slave %{_bindir}/modulecmd modulecmd %{_datadir}/Modules/libexec/modulecmd.tcl

%post compat
%{_sbindir}/update-alternatives \
  --install %{_sysconfdir}/profile.d/modules.sh modules.sh %{_datadir}/Modules/init/profile-compat.sh 10 \
  --slave %{_sysconfdir}/profile.d/modules.csh modules.csh %{_datadir}/Modules/init/profile-compat.csh \
  --slave %{_bindir}/modulecmd modulecmd %{_datadir}/Modules/libexec/modulecmd-compat

%postun
if [ $1 -eq 0 ] ; then
  %{_sbindir}/update-alternatives --remove modules.sh %{_datadir}/Modules/init/profile.sh
fi

%postun compat
if [ $1 -eq 0 ] ; then
  %{_sbindir}/update-alternatives --remove modules.sh %{_datadir}/Modules/init/profile-compat.sh
fi
%endif


%files
%if 0%{?rhel} && 0%{?rhel} <= 6
%doc COPYING.GPLv2
%else
%license COPYING.GPLv2
%endif
%doc ChangeLog NEWS README doc/diff_with_c-version.txt
%{_sysconfdir}/modulefiles
%if 0%{?fedora}
%ghost %{_sysconfdir}/profile.d/modules.csh
%ghost %{_sysconfdir}/profile.d/modules.sh
%ghost %{_bindir}/modulecmd
%else
%{_sysconfdir}/profile.d/modules.csh
%{_sysconfdir}/profile.d/modules.sh
%{_bindir}/modulecmd
%endif
%{_bindir}/envml
%dir %{_datadir}/Modules
%{_datadir}/Modules/bin
%dir %{_datadir}/Modules/libexec
%{_datadir}/Modules/libexec/modulecmd.tcl
%dir %{_datadir}/Modules/init
%config(noreplace) %{_datadir}/Modules/init/*
%config(noreplace) %{_datadir}/Modules/init/.modulespath
%{_datadir}/Modules/modulefiles
%{_datadir}/modulefiles
%{_mandir}/man1/module.1.gz
%{_mandir}/man4/modulefile.4.gz
%{macrosdir}/macros.%{name}

%files compat
%doc ChangeLog-compat NEWS-compat
%{_datadir}/Modules/libexec/modulecmd-compat
%{_mandir}/man1/module-compat.1.gz
%{_mandir}/man4/modulefile-compat.4.gz


%changelog
* Mon Sep 18 2017 Xavier Delaruelle <xavier.delaruelle@cea.fr> - 4.0.0-0.1.beta
- Update to 4.0.0-beta
- Define compat subpackage to provide 3.2 compatiblity version also
  provided in source tarball
- Add condition statements to either build on Fedora and EL systems

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.10-23
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.10-22
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Mar 16 2017 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-21
- Use alternatives for man pages as well

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.10-20
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Mon Dec 19 2016 Miro Hrončok <mhroncok@redhat.com> - 3.2.10-19
- Rebuild for Python 3.6

* Sun Dec 4 2016 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-18
- Fix compilation with -Werror=implicit-function-declaration
- Use %%license

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 3.2.10-17
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Jul 13 2015 Orion Poplwski <orion@cora.nwra.com> - 3.2.10-16
- Add patch to fix unload from loaded modulefile (bug #1117334)

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.10-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Mar 2 2015 Orion Poplwski <orion@cora.nwra.com> - 3.2.10-14
- Fix createmodule.sh to handle exported functions (bug #1197321)
- Handle more prefix/suffix cases in createmodule.{sh,py} (bug #1079341)

* Wed Jan 28 2015 Orion Poplwski <orion@cora.nwra.com> - 3.2.10-13
- Add patch for python 3 support, use python3 for createmodule.py on F22

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.10-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.10-11
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Tue May 27 2014 Orion Poplwski <orion@cora.nwra.com> - 3.2.10-10
- Add patch to support Tcl 8.6

* Wed May 21 2014 Jaroslav Škarvada <jskarvad@redhat.com> - 3.2.10-10
- Rebuilt for https://fedoraproject.org/wiki/Changes/f21tcl86

* Mon Apr 14 2014 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-9
- Use alternatives for /etc/profile.d/modules.{csh,sh}
- Add /usr/share/modulefiles to MODULEPATH
- Add rpm macro to define %%_modulesdir

* Mon Dec 23 2013 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-8
- Fix -Werror=format-security (bug #1037053)

* Wed Sep 4 2013 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-7
- Update createmodule scripts to handle more path like variables (bug #976647)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.10-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Tue May 14 2013 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-5
- Really do not replace modified profile.d scripts (bug #962762)
- Specfile cleanup

* Wed Apr 17 2013 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-4
- Do not replace modified profile.d scripts (bug #953199)

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.10-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Jan 15 2013 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-2
- Add patch to comment out stray module use in modules file when not using
  versioning (bug #895555)
- Add patch to fix module clear command (bug #895551)
- Add patch from modules list to add completion to avail command

* Fri Dec 21 2012 Orion Poplawski <orion@cora.nwra.com> - 3.2.10-1
- Update to 3.2.10
- Drop regex patch

* Wed Oct 31 2012 Orion Poplawski <orion@cora.nwra.com> - 3.2.9c-5
- Updated createmodule.sh, added createmodule.py, can handle path prefixes

* Fri Aug 24 2012 Orion Poplawski <orion@cora.nwra.com> - 3.2.9c-4
- Add patch to fix segfault from Tcl RexExp handling (bug 834580)

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.9c-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.9c-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Nov 29 2011 Orion Poplawski <orion@cora.nwra.com> - 3.2.9c-1
- Update to 3.2.9c (fixes bug 753760)

* Tue Nov 22 2011 Orion Poplawski <orion@cora.nwra.com> - 3.2.9b-2
- Make .modulespath a config file

* Tue Nov 15 2011 Orion Poplawski <orion@cora.nwra.com> - 3.2.9b-1
- Update to 3.2.9b

* Fri Nov 11 2011 Orion Poplawski <orion@cora.nwra.com> - 3.2.9a-2
- Add %%check section

* Fri Nov 11 2011 Orion Poplawski <orion@cora.nwra.com> - 3.2.9a-1
- Update to 3.2.9a
- Drop strcpy patch

* Thu Sep 22 2011 Orion Poplawski <orion@cora.nwra.com> - 3.2.8a-3
- Add patch to fix overlapping strcpy() in Remove_Path, hopefully fixes
  bug 737043

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.8a-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Oct 4 2010 Orion Poplawski <orion@cora.nwra.com> - 3.2.8a-1
- Update to 3.2.8a, changes --with-def-man-path to --with-man-path

* Mon Oct 4 2010 Orion Poplawski <orion@cora.nwra.com> - 3.2.8-1
- Update to 3.2.8
- Drop mandir patch, use --with-def-man-path

* Thu Jan 7 2010 Orion Poplawski <orion@cora.nwra.com> - 3.2.7b-7
- Add patch to set a sane default MANPATH
- Add createmodule.sh utility script for creating modulefiles
 
* Mon Nov 30 2009 Orion Poplawski <orion@cora.nwra.com> - 3.2.7b-6
- Add Requires: propcs (bug #54272)

* Mon Oct 26 2009 Orion Poplawski <orion@cora.nwra.com> - 3.2.7b-5
- Don't assume different shell init scripts exist (bug #530770)

* Fri Oct 23 2009 Orion Poplawski <orion@cora.nwra.com> - 3.2.7b-4
- Don't load bash init script when bash is running as "sh" (bug #529745)

* Mon Oct 19 2009 Orion Poplawski <orion@cora.nwra.com> - 3.2.7b-3
- Support different flavors of "sh" (bug #529493)

* Wed Sep 23 2009 Orion Poplawski <orion@cora.nwra.com> - 3.2.7b-2
- Add patch to fix modulecmd path in init files

* Wed Sep 23 2009 Orion Poplawski <orion@cora.nwra.com> - 3.2.7b-1
- Update to 3.2.7b

* Mon Sep 21 2009 Orion Poplawski <orion@cora.nwra.com> - 3.2.7-1
- Update to 3.2.7, fixes bug #524475
- Drop versioning patch fixed upstream

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.6-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 3.2.6-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Sep 3 2008 - Orion Poplawski <orion@cora.nwra.com> - 3.2.6-6
- Change %%patch -> %%patch0

* Fri Mar 14 2008 - Orion Poplawski <orion@cora.nwra.com> - 3.2.6-5
- Add BR libX11-devel so modulecmd can handle X resources

* Wed Mar  5 2008 - Orion Poplawski <orion@cora.nwra.com> - 3.2.6-4
- Add patch to fix extraneous version path entry properly
- Use --with-module-path to point to /etc/modulefiles for local modules,
  this also fixes bug #436041

* Sat Feb  9 2008 - Orion Poplawski <orion@cora.nwra.com> - 3.2.6-3
- Rebuild for gcc 3.4

* Thu Jan 03 2008 - Alex Lancaster <alexlan at fedoraproject.org> - 3.2.6-2
- Rebuild for new Tcl (8.5).

* Fri Nov  2 2007 - Orion Poplawski <orion@cora.nwra.com> - 3.2.6-1
- Update to 3.2.6

* Tue Aug 21 2007 - Orion Poplawski <orion@cora.nwra.com> - 3.2.5-2
- Update license tag to GPLv2

* Fri Feb 16 2007 - Orion Poplawski <orion@cora.nwra.com> - 3.2.5-1
- Update to 3.2.5

* Wed Feb 14 2007 - Orion Poplawski <orion@cora.nwra.com> - 3.2.4-2
- Rebuild for Tcl downgrade

* Fri Feb 09 2007 - Orion Poplawski <orion@cora.nwra.com> - 3.2.4-1
- Update to 3.2.4

* Wed Dec 20 2006 - Orion Poplawski <orion@cora.nwra.com> - 3.2.3-3
- Add --with-version-path to set VERSIONPATH (bug 220260)

* Tue Aug 29 2006 - Orion Poplawski <orion@cora.nwra.com> - 3.2.3-2
- Rebuild for FC6

* Fri Jun  2 2006 - Orion Poplawski <orion@cora.nwra.com> - 3.2.3-1
- Update to 3.2.3

* Fri May  5 2006 - Orion Poplawski <orion@cora.nwra.com> - 3.2.2-1
- Update to 3.2.2

* Fri Mar 24 2006 - Orion Poplawski <orion@cora.nwra.com> - 3.2.1-1
- Update to 3.2.1

* Thu Feb  9 2006 - Orion Poplawski <orion@cora.nwra.com> - 3.2.0p1-1
- Update to 3.2.0p1

* Fri Jan 27 2006 - Orion Poplawski <orion@cora.nwra.com> - 3.2.0-2
- Add profile.d links

* Tue Jan 24 2006 - Orion Poplawski <orion@cora.nwra.com> - 3.2.0-1
- Fedora Extras packaging
