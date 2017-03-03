# CVC4 1.4 and later need a modified glpk, unavailable in Fedora.  Therefore,
# we currently build without glpk support.

Name:           cvc4
Version:        1.4
Release:        14%{?dist}
Summary:        Automatic theorem prover for SMT problems

# License breakdown:
# - Files containing code under the Boost license:
#   o src/util/channel.h
#   o examples/hashsmt/sha1.hpp
# - Files containing code under the BSD license:
#   o proofs/lfsc_checker/*
#   o src/parser/antlr_input_imports.cpp
#   o src/parser/bounded_token_buffer.cpp
# - All other files are distributed under the MIT license
# But we link with readline, so it all gets subsumed by GPLv3+ anyway.
License:        GPLv3+
URL:            http://cvc4.cs.stanford.edu/
Source0:        http://cvc4.cs.nyu.edu/builds/src/%{name}-%{version}.tar.gz
# Fix some doxygen problems.  Upstream plans to fix this differently.
Patch0:         %{name}-doxygen.patch
# Adapt to the way the Fedora ABC package is constructed.
Patch1:         %{name}-abc.patch
# Fix some mixed signed/unsigned comparisons
Patch2:         %{name}-signed.patch
# Fix some broken boolean expressions
Patch3:         %{name}-boolean.patch
# Fix out-of-bounds array accesses in the minisat code
Patch4:         %%{name}-minisat.patch

BuildRequires:  abc-devel
BuildRequires:  antlr3-C-devel
BuildRequires:  antlr3-tool
BuildRequires:  boost-devel
BuildRequires:  chrpath
BuildRequires:  cxxtest
BuildRequires:  doxygen-latex
BuildRequires:  gcc-c++
BuildRequires:  ghostscript-core
BuildRequires:  gmp-devel
BuildRequires:  java-devel
BuildRequires:  jpackage-utils
BuildRequires:  perl
BuildRequires:  python2
BuildRequires:  readline-devel
BuildRequires:  swig

Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

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

%package doc
Summary:        Interface documentation for %{name}
Provides:       bundled(jquery)

%description doc
Interface documentation for %{name}.

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

%prep
%setup -q
# The rpm patch macro doesn't understand -T, and we need it to to avoid
# regenerating the very files we're trying to patch.
patch -p0 -T < %{PATCH0}
%patch1
%patch2
%patch3
%patch4

# Don't change the build flags we want to use, avoid hardcoded rpaths, adapt to
# antlr 3.5, and allow boost to use g++ 5.0 and higher.
sed -e '/^if test "$enable_debug_symbols"/,/fi/d' \
    -e 's,^hardcode_libdir_flag_spec=.*,hardcode_libdir_flag_spec="",g' \
    -e 's,runpath_var=LD_RUN_PATH,runpath_var=DIE_RPATH_DIE,g' \
    -e 's,\([^.]\)3\.4,\13.5,g' \
    -e 's,\$ac_cpp conftest,$ac_cpp -P conftest,' \
    -e '/gcc48/i\    "defined __GNUC__ && __GNUC__ == 7 && __GNUC_MINOR__ == 0 && !defined __ICC @ gcc70" \\\n    "defined __GNUC__ && __GNUC__ == 6 && __GNUC_MINOR__ == 0 && !defined __ICC @ gcc60" \\\n    "defined __GNUC__ && __GNUC__ == 5 && __GNUC_MINOR__ == 3 && !defined __ICC @ gcc53" \\\n    "defined __GNUC__ && __GNUC__ == 5 && __GNUC_MINOR__ == 2 && !defined __ICC @ gcc52" \\\n    "defined __GNUC__ && __GNUC__ == 5 && __GNUC_MINOR__ == 1 && !defined __ICC @ gcc51" \\\n    "defined __GNUC__ && __GNUC__ == 5 && __GNUC_MINOR__ == 0 && !defined __ICC @ gcc50" \\' \
    -i configure

# Change the Java installation paths for Fedora and fix FTBFS
sed -e "s|^\(javalibdir =.*\)jni|\1java/%{name}|" \
    -e 's/ -Wno-all//' \
    -i src/bindings/Makefile.in

# Fix access to an uninitialized variable
sed -e 's/Kind k;/Kind k = kind::UNDEFINED_KIND;/' \
    -i src/parser/cvc/generated/CvcParser.c

# Make lfsc documentation available
cp -p proofs/lfsc_checker/AUTHORS AUTHORS.lfsc
cp -p proofs/lfsc_checker/COPYING COPYING.lfsc
cp -p proofs/lfsc_checker/NEWS NEWS.lfsc
cp -p proofs/lfsc_checker/README README.lfsc

# Help the documentation generator
cp -p COPYING src/bindings/compat/c

# Preserve timestamps when installing
for fil in $(find . -name Makefile\*); do
  sed -i 's/$(install_sh) -c/$(install_sh) -p/' $fil
done

%build
export CPPFLAGS="-I%{_jvmdir}/java/include -I%{_jvmdir}/java/include/linux -I%{_includedir}/abc"
if [ "%{__isa_bits}" == "64" ]; then
CPPFLAGS+=" -DLIN64"
else
CPPFLAGS+=" -DLIN"
fi
export CFLAGS="%{optflags} -fsigned-char"
export CXXFLAGS="%{optflags} -fsigned-char -std=gnu++98"
%configure --enable-gpl --enable-proof --enable-language-bindings=all \
  --disable-silent-rules --with-portfolio --with-abc --with-abc-dir=%{_prefix} \
  --with-readline --without-compat

# Workaround libtool reordering -Wl,--as-needed after all the libraries
BUILDS=$(echo $PWD/builds/*linux*/*abc*)
sed -i 's/CC=.g../& -Wl,--as-needed/' $BUILDS/libtool

make %{?_smp_mflags}
make doc

%install
%make_install

# Remove unwanted libtool files
find %{buildroot}%{_libdir} -name \*.la | xargs rm -f

# Remove empty directories for language bindings that do not yet exist
rm -fr %{buildroot}%{_libdir}/{csharp,ocaml,perl5,php,pyshared,ruby,tcltk}
rm -fr %{buildroot}%{_datadir}/{csharp,perl5,php,pyshared}

# Make the Java installation match Fedora requirements
if [ "%{_libdir}/java" != "%{_jnidir}" ]; then
  mkdir -p %{buildroot}%{_jnidir}
  mv %{buildroot}%{_libdir}/java/cvc4 %{buildroot}%{_jnidir}
  rmdir %{buildroot}%{_libdir}/java
fi

# Remove still more hardcoded rpaths
chrpath -d %{buildroot}%{_bindir}/* \
           %{buildroot}%{_libdir}/lib%{name}*.so.*.*.* \
           %{buildroot}%{_jnidir}/%{name}/lib%{name}*.so.*.*.*

# Help the debuginfo generator
BUILDS=$(echo $PWD/builds/*linux*/*abc*)
for dir in decision expr main parser printer prop smt theory theory/arith \
    theory/arrays theory/booleans theory/bv theory/datatypes theory/idl \
    theory/quantifiers theory/rewriterules theory/strings theory/uf; do
  ln -s $PWD/src/$dir/options $BUILDS/src/$dir
done
ln -s production-abc-proof/src $BUILDS/../src
ln -s $PWD/src/options/base_options $BUILDS/src/options
ln -s $PWD/src/options/base_options_template.cpp $BUILDS/src/options
ln -s $PWD/src/options/options_holder_template.h $BUILDS/src/options
ln -s $PWD/src/options/options_template.cpp $BUILDS/src/options
ln -s $PWD/src/smt/smt_options_template.cpp $BUILDS/src/smt

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%check
# The tests use a large amount of stack space
ulimit -s unlimited

# Do not rebuild when checking
BUILDS=$(echo $PWD/builds/*linux*/*abc*)
sed -e 's/\(units.*:\) all/\1/' \
    -e 's/\(regress.*:\) all/\1/' \
    -i $BUILDS/Makefile $BUILDS/Makefile.builds

export LD_LIBRARY_PATH=$PWD/builds%{_libdir}
make check 

%files
%doc AUTHORS AUTHORS.lfsc NEWS NEWS.lfsc README README.lfsc RELEASE-NOTES THANKS
%license COPYING.lfsc
%{_bindir}/*
%{_datadir}/%{name}/
%{_mandir}/man1/*
%{_mandir}/man5/*

%files doc
%doc doc/doxygen/*

%files libs
%license COPYING
%{_libdir}/lib%{name}*.so.*

%files devel
%{_includedir}/%{name}/
%{_libdir}/lib%{name}*.so
%{_mandir}/man3/*

%files java
%{_javadir}/*.jar
%{_jnidir}/%{name}/

%changelog
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
