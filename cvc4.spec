%ifarch %{ix86} x86_64 ppc ppc64 %{arm}
%global have_perftools 1
%endif

Name:           cvc4
Version:        1.3
Release:        4%{?dist}
Summary:        Automatic theorem prover for SMT problems

# License breakdown:
# - Files containing code under the Boost license:
#   o src/util/channel.h
#   o examples/hashsmt/sha1.hpp
# - Files containing code under the BSD license:
#   o src/parser/antlr_input_imports.cpp
#   o src/parser/bounded_token_buffer.cpp
# - All other files are distributed under the MIT license
License:        MIT and BSD and Boost
URL:            http://cvc4.cs.nyu.edu/web/
Source0:        http://cvc4.cs.nyu.edu/builds/src/%{name}-%{version}.tar.gz
# Updated *.plf files from upstream.  These are needed only for the self-tests.
Source1:        smt.plf
Source2:        sat.plf
Source3:        th_base.plf
# Fix some doxygen problems.  Upstream plans to fix this differently.
Patch0:         %{name}-doxygen.patch

BuildRequires:  antlr3-C-devel
BuildRequires:  antlr3-tool
BuildRequires:  boost-devel
BuildRequires:  chrpath
BuildRequires:  cxxtest
BuildRequires:  doxygen-latex
BuildRequires:  ghostscript
BuildRequires:  glpk-devel
BuildRequires:  gmp-devel
%if 0%{?have_perftools}
BuildRequires:  gperftools-devel
%endif
BuildRequires:  java-devel >= 1:1.6.0
BuildRequires:  jpackage-utils
BuildRequires:  lfsc
BuildRequires:  perl
BuildRequires:  python
BuildRequires:  readline-devel
BuildRequires:  swig

Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Requires:       lfsc

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
# The rpm patch macro doesn't understand -T, and we need to it to avoid
# regenerating the very files we're trying to patch.
patch -p0 -T < %{PATCH0}

# Don't change the build flags we want to use and avoid hardcoded rpaths
sed -e '/^if test "$enable_debug_symbols"/,/fi/d' \
    -e 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' \
    -e 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' \
    -i configure

# Change the Java installation paths for Fedora
sed -i "s|^\(javalibdir =.*\)jni|\1java/%{name}|" src/bindings/Makefile.in

%build
%configure --enable-proof --enable-language-bindings=all --with-portfolio \
%if 0%{?have_perftools}
  --with-google-perftools \
%endif
  --with-glpk --without-compat \
  CPPFLAGS="-I%{_jvmdir}/java/include -I%{_jvmdir}/java/include/linux -DFEDORA_GLPK_ITCNT -Dlpx_get_int_parm(x,y)=glp_get_it_cnt(x)" \
  LFSCARGS="%{_datadir}/lfsc/sat.plf"

# Workaround libtool reordering -Wl,--as-needed after all the libraries
sed -i 's/CC=.g../& -Wl,--as-needed/' builds/*-linux-gnu/default-proof/libtool

# Workaround insufficiently quoted CPPFLAGS
find builds -name Makefile | xargs sed -i 's/-Dlpx.*glp_get_it_cnt(x)/"&"/'

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
BUILDS=builds/*-*-linux-gnu
for dir in decision expr main parser printer prop smt theory theory/arith \
    theory/arrays theory/booleans theory/bv theory/datatypes theory/idl \
    theory/quantifiers theory/rewriterules theory/strings theory/uf; do
  ln -s $PWD/src/$dir/options $BUILDS/default-proof/src/$dir
done
ln -s default-proof/src $BUILDS
ln -s $PWD/src/options/base_options $BUILDS/default-proof/src/options
ln -s $PWD/src/options/base_options_template.cpp $BUILDS/src/options
ln -s $PWD/src/options/options_holder_template.h $BUILDS/src/options
ln -s $PWD/src/options/options_template.cpp $BUILDS/src/options
ln -s $PWD/src/smt/smt_options_template.cpp $BUILDS/src/smt

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig

%check
# The tests use a large amount of stack space
ulimit -s unlimited

# The tests require unreleased *.plf files from upstream
for mk in $(find builds/*-*-linux-gnu/default-proof/test -name Makefile)
do
  sed -e 's,^\(LFSCARGS =\).*,\1 %{SOURCE1} %{SOURCE2} %{SOURCE3},' \
      -e 's,^\(TESTS_ENVIRONMENT = LFSC=\)".*",\1"lfsc %{SOURCE1} %{SOURCE2} %{SOURCE3}",' \
      -i $mk
done

make check 

%files
%doc AUTHORS NEWS README RELEASE-NOTES THANKS
%{_bindir}/*
%{_mandir}/man1/*
%{_mandir}/man5/*

%files doc
%doc doc/doxygen/*

%files libs
%doc COPYING
%{_libdir}/lib%{name}*.so.*

%files devel
%{_includedir}/%{name}/
%{_libdir}/lib%{name}*.so
%{_mandir}/man3/*

%files java
%{_javadir}/*.jar
%{_jnidir}/%{name}/

%changelog
* Thu Mar  6 2014 Jerry James <loganjerry@gmail.com> - 1.3-4
- Merge changes from Dan Horák to fix secondary arch builds

* Tue Feb  4 2014 Jerry James <loganjerry@gmail.com> - 1.3-3
- glibc Provides /sbin/ldconfig, not /usr/sbin/ldconfig

* Mon Jan 27 2014 Jerry James <loganjerry@gmail.com> - 1.3-2
- Install JNI objects in %%{_jnidir}
- The documentation is arch-specific after all

* Wed Jan 22 2014 Jerry James <loganjerry@gmail.com> - 1.3-1
- Initial RPM
