# CVC4 1.4 and later need a modified glpk, unavailable in Fedora.  Therefore,
# we currently build without glpk support.

Name:           cvc4
Version:        1.7
Release:        8%{?dist}
Summary:        Automatic theorem prover for SMT problems

# License breakdown:
# - Files containing code under the Boost license:
#   o src/util/channel.h
#   o examples/hashsmt/sha1.hpp
# - Files containing code under the BSD license:
#   o src/parser/antlr_input_imports.cpp
#   o src/parser/bounded_token_buffer.cpp
# - All other files are distributed under the MIT license
License:        Boost and BSD and MIT
URL:            http://cvc4.cs.stanford.edu/
Source0:        https://github.com/CVC4/CVC4/archive/%{version}/%{name}-%{version}.tar.gz
# Fix detection of ABC
Patch0:         %{name}-abc.patch
# Do not override Fedora flags
Patch1:         %{name}-flags.patch
# Adapt to swig 4
Patch2:         %{name}-swig4.patch
# Fix drat signature wrt side condition return types
# https://github.com/CVC4/CVC4/commit/57524fd9f204f8e85e5e37af1444a6f76d809aee
Patch3:         %{name}-drat.patch

BuildRequires:  abc-devel
BuildRequires:  antlr3-C-devel
BuildRequires:  antlr3-tool
BuildRequires:  boost-devel
BuildRequires:  cadical-devel
BuildRequires:  cmake
BuildRequires:  cryptominisat-devel
BuildRequires:  cxxtest
BuildRequires:  drat2er-devel
BuildRequires:  gcc-c++
BuildRequires:  ghostscript
BuildRequires:  gmp-devel
BuildRequires:  java-devel
BuildRequires:  jpackage-utils
BuildRequires:  lfsc-devel
BuildRequires:  libtool
BuildRequires:  perl-interpreter
BuildRequires:  python3-devel
BuildRequires:  readline-devel
BuildRequires:  swig
BuildRequires:  symfpu-devel

Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

# This can be removed when Fedora 30 reaches EOL
Obsoletes:      %{name}-doc < 1.7
Provides:       %{name}-doc = %{version}-%{release}

%description
CVC4 is an efficient open-source automatic theorem prover for
satisfiability modulo theories (SMT) problems.  It can be used to prove
the validity (or, dually, the satisfiability) of first-order formulas in
a large number of built-in logical theories and their combination.

CVC4 is the fourth in the Cooperating Validity Checker family of tools
(CVC, CVC Lite, CVC3) but does not directly incorporate code from any
previous version.  A joint project of NYU and U Iowa, CVC4 aims to
support the  features of CVC3 and SMT-LIBv2 while optimizing the design
of the core system architecture and decision procedures to take
advantage of recent engineering and algorithmic advances.

CVC4 is intended to be an open and extensible SMT engine, and it can be
used as a stand-alone tool or as a library, with essentially no limit on
its use for research or commercial purposes.

%package devel
Summary:        Headers and other files for developing with %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description devel
Header files and library links for developing applications that use %{name}.

%package libs
Summary:        Library containing an automatic theorem prover for SMT problems

%description libs
Library containing the core of the %{name} automatic theorem prover for
SMT problems.

%package java
Summary:        Java interface to %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Requires:       java-headless
Requires:       jpackage-utils

%description java
Java interface to %{name}.

%package python3
Summary:        Python 3 interface to %{name}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description python3
Python 3 interface to %{name}.

%prep
%autosetup -p0 -n CVC4-%{version}

# The Java interface uses type punning
sed -i '/include_directories/aadd_compile_options("-fno-strict-aliasing")' \
    src/bindings/java/CMakeLists.txt

# The header file installation script does not know about DESTDIR
sed -i 's/\${CMAKE_INSTALL_PREFIX}/\\$ENV{DESTDIR}&/' src/CMakeLists.txt

# Fix installation directory on 64-bit arches
if [ "%{_lib}" = "lib64" ]; then
  sed -i 's/DESTINATION lib/&64/' src/CMakeLists.txt src/parser/CMakeLists.txt
fi

# One test exhausts all memory on 32-bit platforms; skip it
%ifarch %{arm} %{ix86}
sed -i '/replaceall-len-c/d' test/regress/CMakeLists.txt
%endif

%build
pyinc=$(python3-config --includes | sed -r 's/-I([^[:blank:]]+)[[:blank:]]*.*/\1/')
pylib=$(ls -1 %{_libdir}/libpython3.*.so)
export CFLAGS="%{optflags} -fsigned-char -DABC_USE_STDINT_H -I%{_jvmdir}/java/include -I%{_jvmdir}/java/include/linux -I%{_includedir}/abc"
export CXXFLAGS="$CFLAGS"
%cmake \
  -DCMAKE_SKIP_RPATH:BOOL=YES \
  -DCMAKE_SKIP_INSTALL_RPATH:BOOL=YES \
  -DBUILD_BINDINGS_JAVA:BOOL=ON \
  -DBUILD_BINDINGS_PYTHON:BOOL=ON \
  -DENABLE_GPL:BOOL=ON \
  -DENABLE_OPTIMIZED:STRING=ON \
  -DENABLE_PORTFOLIO:STRING=ON \
  -DENABLE_PROOFS:STRING=ON \
  -DENABLE_SHARED:STRING=ON \
  -DUSE_ABC:STRING=ON \
  -DABC_DIR:STRING=%{_prefix} \
  -DUSE_CADICAL:BOOL=ON \
  -DCADICAL_DIR:STRING=%{_prefix} \
  -DUSE_CRYPTOMINISAT:BOOL=ON \
  -DCRYPTOMINISAT_DIR:STRING=%{_prefix} \
  -DUSE_DRAT2ER:BOOL=ON \
  -DDRAT2ER_DIR:STRING=%{_prefix} \
  -DDrat2Er_INCLUDE_DIR:STRING=%{_includedir}/drat2er \
  -DDrat2Er_LIBRARIES:STRING=-ldrat2er \
  -DDratTrim_LIBRARIES:STRING=-ldrat2er \
  -DUSE_LFSC:BOOL=ON \
  -DLFSC_DIR:STRING=%{_prefix} \
  -DUSE_PYTHON3:BOOL=ON \
  -DUSE_READLINE:STRING=ON \
  -DUSE_SYMFPU:BOOL=ON \
  -DSYMFPU_DIR:STRING=%{_prefix} \
  -DPYTHON_EXECUTABLE:FILEPATH=%{_bindir}/python%{python3_version} \
  -DPYTHON_LIBRARY:FILEPATH=$pylib \
  -DPYTHON_INCLUDE_DIR:FILEPATH=$pyinc \
  .

# Tell swig to build for python 3
sed -i 's/swig -python/& -py3/' \
  src/bindings/python/CMakeFiles/CVC4_swig_compilation.dir/build.make

make %{?_smp_mflags}
make doc

%install
%make_install

# BUG: CVC4 1.7 does not install the Java interface
mkdir -p %{buildroot}%{_javadir}
cp -p src/bindings/java/CVC4.jar %{buildroot}%{_javadir}
mkdir -p %{buildroot}%{_jnidir}/%{name}
cp -p src/bindings/java/libcvc4jni.so %{buildroot}%{_jnidir}/%{name}

%check
# The tests use a large amount of stack space.
# Only do this on s390x to workaround bz 1688841.
%ifarch s390x
ulimit -s unlimited
%endif

# Fix the Java test's access to the JNI object it needs
sed 's,loadLibrary("cvc4jni"),load("%{buildroot}%{_jnidir}/%{name}/libcvc4jni.so"),' \
    -i test/system/CVC4JavaTest.java

export LC_ALL=C.UTF-8
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}
make check 

%files
%doc AUTHORS NEWS README.md THANKS
%{_bindir}/%{name}
%{_bindir}/p%{name}
%{_datadir}/%{name}/
%{_mandir}/man1/%{name}.1*
%{_mandir}/man1/p%{name}.1*
%{_mandir}/man5/%{name}.5*

%files libs
%license COPYING licenses/channel.h-LICENSE
%{_libdir}/lib%{name}.so.6
%{_libdir}/lib%{name}parser.so.6

%files devel
%{_includedir}/%{name}/
%{_libdir}/lib%{name}.so
%{_libdir}/lib%{name}parser.so
%{_mandir}/man3/*

%files java
%{_javadir}/CVC4.jar
%{_jnidir}/%{name}/

%files python3
%{python3_sitearch}/CVC4.py
%{python3_sitearch}/_CVC4.so
%{python3_sitearch}/__pycache__/CVC4.*

%changelog
* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 1.7-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Mon Nov 11 2019 Jerry James <loganjerry@gmail.com> - 1.7-7
- Rebuild for cadical 1.2.1

* Mon Sep  9 2019 Jerry James <loganjerry@gmail.com> - 1.7-6
- Add -drat patch to fix build with latest lfsc

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 1.7-5
- Rebuilt for Python 3.8

* Wed Jul 24 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.7-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Thu Jul 18 2019 Jerry James <loganjerry@gmail.com> - 1.7-3
- Rebuild for cadical 1.0.3 (bz 1731031)

* Sat Jun 29 2019 Jerry James <loganjerry@gmail.com> - 1.7-2
- Fix finding the python include dir and lib (bz 1724142)

* Wed Jun 12 2019 Jerry James <loganjerry@gmail.com> - 1.7-1
- New upstream release
- Drop -autoconf, -cadical, -doxygen, -symfpu, and -vec patches
- Drop -doc subpackage; upstream no longer supports doxygen
- Build with python 3 instead of python 2
- Build with drat2er support
- Add -abc and -flags patches
- Add -swig4 patch (bz 1707353)

* Sun Feb 17 2019 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1.6-6
- Rebuild for readline 8.0

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 1.6-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Tue Jan 29 2019 Jonathan Wakely <jwakely@redhat.com> - 1.6-4
- Rebuilt for Boost 1.69

* Mon Nov 26 2018 Jerry James <loganjerry@gmail.com> - 1.6-3
- Rebuild for updated abc

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jul 10 2018 Jerry James <loganjerry@gmail.com> - 1.6-1
- New upstream release

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.5-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Feb  1 2018 Jerry James <loganjerry@gmail.com> - 1.5-5
- Fix FTBFS with automake 1.5.1 (bz 1482152)

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.5-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 21 2017 Kalev Lember <klember@redhat.com> - 1.5-2
- Rebuilt for Boost 1.64

* Sat Jul 15 2017 Jerry James <loganjerry@gmail.com> - 1.5-1
- New upstream release
- Drop upstreamed patches: -signed, -boolean, -minisat
- Add -constant patch to fix undefined symbols in the JNI shared object
- Add cryptominisat4 support

* Mon May 15 2017 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4-15
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_27_Mass_Rebuild

* Fri Mar  3 2017 Jerry James <loganjerry@gmail.com> - 1.4-14
- Fix FTBFS (bz 1427891)

* Tue Feb 07 2017 Kalev Lember <klember@redhat.com> - 1.4-13
- Rebuilt for Boost 1.63

* Thu Jan 12 2017 Igor Gnatenko <ignatenko@redhat.com> - 1.4-12
- Rebuild for readline 7.x

* Tue May 17 2016 Jonathan Wakely <jwakely@redhat.com> - 1.4-11
- Rebuilt for linker errors in boost (#1331983)

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.4-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Fri Jan 15 2016 Jonathan Wakely <jwakely@redhat.com> - 1.4-9
- Rebuilt for Boost 1.60

* Thu Aug 27 2015 Jonathan Wakely <jwakely@redhat.com> - 1.4-8
- Rebuilt for Boost 1.59

* Wed Jul 29 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4-7
- Rebuilt for https://fedoraproject.org/wiki/Changes/F23Boost159

* Wed Jul 22 2015 David Tardon <dtardon@redhat.com> - 1.4-6
- rebuild for Boost 1.58

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.4-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Sat May 02 2015 Kalev Lember <kalevlember@gmail.com> - 1.4-4
- Rebuilt for GCC 5 C++11 ABI change

* Fri Mar 20 2015 Jerry James <loganjerry@gmail.com> - 1.4-3
- Don't use perftools at all due to random weirdness on multiple platforms
- Also Obsoletes/Provides lfsc-devel

* Wed Mar 11 2015 Jerry James <loganjerry@gmail.com> - 1.4-2
- Add -boolean, -minisat, and -signed patches to fix test failures
- Fix boost detection with g++ 5.0
- Fix access to an uninitialized variable
- Help the documentation generator find COPYING
- Build with -fsigned-char to fix the arm build
- Prevent rebuilds while running checks
- Remove i686 from have_perftools due to test failures

* Tue Jan 27 2015 Petr Machata <pmachata@redhat.com> - 1.4-2
- Rebuild for boost 1.57.0

* Thu Jan  1 2015 Jerry James <loganjerry@gmail.com> - 1.4-1
- New upstream release
- Drop updated test files, now included upstream
- Drop obsolete workarounds for glpk compatibility
- Drop lfsc BR/R, as it has been incorporated into cvc4

* Fri Aug 22 2014 Jerry James <loganjerry@gmail.com> - 1.3-7
- Remove arm platforms from have_perftools due to bz 1109309

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.3-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri May 23 2014 David Tardon <dtardon@redhat.com> - 1.3-5
- rebuild for boost 1.55.0

* Thu Mar  6 2014 Jerry James <loganjerry@gmail.com> - 1.3-4
- Merge changes from Dan Horák to fix secondary arch builds

* Tue Feb  4 2014 Jerry James <loganjerry@gmail.com> - 1.3-3
- glibc Provides /sbin/ldconfig, not /usr/sbin/ldconfig

* Mon Jan 27 2014 Jerry James <loganjerry@gmail.com> - 1.3-2
- Install JNI objects in %%{_jnidir}
- The documentation is arch-specific after all

* Wed Jan 22 2014 Jerry James <loganjerry@gmail.com> - 1.3-1
- Initial RPM
