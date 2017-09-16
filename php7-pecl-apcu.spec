%{!?__pecl: %{expand: %%global __pecl %{_bindir}/pecl}}

%global php_zendabiver %((echo 0; php -i 2>/dev/null | sed -n 's/^PHP Extension => //p') | tail -1)
%global php_version %((echo 0; php-config --version 2>/dev/null) | tail -1)
%global basepkg   %{?basepkg}%{!?basepkg:php}
%global pecl_name apcu
%global with_zts  0%{?__ztsphp:1}

Summary:       APCu - APC User Cache
Name:          %{basepkg}-pecl-apcu
Version:       5.1.8
Release:       2%{?dist}
License:       PHP
Group:         Development/Languages
URL:           http://pecl.php.net/package/APCu
Source:        http://pecl.php.net/get/apcu-%{version}.tgz
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root
Conflicts:     php-mmcache php-eaccelerator
BuildRequires: %{basepkg}-devel >= 5.1.0, httpd-devel, %{basepkg}-pear
Requires(post): %{__pecl}
Requires(postun): %{__pecl}
%if %{?php_zend_api}0
# Require clean ABI/API versions if available (Fedora)
Requires:      php(zend-abi) = %{php_zend_api}
Requires:      php(api) = %{php_core_api}
%else
%if "%{rhel}" == "5"
# RHEL5 where we have php-common providing the Zend ABI the "old way"
Requires:      php-zend-abi = %{php_zendabiver}
%else
# RHEL4 where we have no php-common and nothing providing the Zend ABI...
Requires:      php = %{php_version}
%endif
%endif
Provides:      php-pecl(%{pecl_name}) = %{version}

%if 0%{?fedora} < 20 && 0%{?rhel} < 7
# Filter private shared
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}
%endif

Requires(post): %{__pecl}
Requires(postun): %{__pecl}

%description
APCu is userland caching: APC stripped of opcode caching in preparation for the
deployment of Zend Optimizer+ as the primary solution to opcode caching in
future versions of PHP

%package devel
Summary:       APCu developer files (header)
Group:         Development/Libraries
Requires:      %{name} = %{version}-%{release}
Requires:      php-devel
Provides:      php-pecl-apc-devel = %{version}-%{release}

%description devel
These are the files needed to compile programs using APCu.

%prep
%setup -q -c

%if %{with_zts}
cp -r %{pecl_name}-%{version} %{pecl_name}-%{version}-zts
%endif

%build
pushd %{pecl_name}-%{version}
%{_bindir}/phpize
%configure --enable-apcu-mmap --with-php-config=%{_bindir}/php-config
%{__make} %{?_smp_mflags}
popd

%if %{with_zts}
pushd %{pecl_name}-%{version}-zts
%{_bindir}/zts-phpize
%configure --enable-apcu-mmap --with-php-config=%{_bindir}/zts-php-config
%{__make} %{?_smp_mflags}
popd
%endif

%install
%{__rm} -rf %{buildroot}

pushd %{pecl_name}-%{version}
%{__make} install INSTALL_ROOT=%{buildroot}

popd

%if %{with_zts}
pushd %{pecl_name}-%{version}-zts
%{__make} install INSTALL_ROOT=%{buildroot}
popd

%endif

# Install the package XML file
%{__mkdir_p} %{buildroot}%{pecl_xmldir}
%{__install} -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

# Drop in the bit of configuration
%{__mkdir_p} %{buildroot}%{php_inidir}
%{__cat} > %{buildroot}%{php_inidir}/apcu.ini << 'EOF'
; Enable apcu extension module
extension = apcu.so

; Options for the APCu module version >= 4.0.0

; This can be set to 0 to disable APC. 
apc.enabled=1
; The number of shared memory segments to allocate for the compiler cache. 
apc.shm_segments=1
; The size of each shared memory segment with M/G suffix.
apc.shm_size=64M
; A "hint" about the number of distinct user cache variables to store.
; Set to zero or omit if you're not sure;
apc.entries_hint=4096
; The number of seconds a cache entry is allowed to idle in a slot in case this
; cache entry slot is needed by another entry.
apc.ttl=7200
; use the SAPI request start time for TTL
apc.use_request_time=1
; The number of seconds that a cache entry may remain on the garbage-collection list. 
apc.gc_ttl=3600
; If enabled, the value will be used to determine if a expunge should happen
; when low on resources.
; By default, it will happen if it is less than half full
apc.smart=0
; The mktemp-style file_mask to pass to the mmap module 
apc.mmap_file_mask=/tmp/apc.XXXXXX
; If enabled, APCu attempts to prevent "slamming" of a key.
apc.slam_defense=1
; Defines which serializer should be used. Default is the standard PHP serializer.
apc.serializer='default'
; Setting this enables APC for the CLI version of PHP (Mostly for testing and debugging).
apc.enable_cli=0
; RFC1867 File Upload Progress hook handler
apc.rfc1867=0
apc.rfc1867_prefix =upload_
apc.rfc1867_name=APC_UPLOAD_PROGRESS
apc.rfc1867_freq=0
apc.rfc1867_ttl=3600
; Enables APC handling of signals, such as SIGSEGV, that write core files when signaled. 
; APC will attempt to unmap the shared memory segment in order to exclude it from the core file
apc.coredump_unmap=0
EOF

%if %{with_zts}
%{__mkdir_p} %{buildroot}%{php_ztsinidir}
%{__cp} %{buildroot}%{php_inidir}/apcu.ini %{buildroot}%{php_ztsinidir}/apcu.ini
%endif

%check
pushd %{pecl_name}-%{version}
TEST_PHP_EXECUTABLE=$(which php) php run-tests.php \
    -n -q -d extension_dir=modules \
    -d extension=apcu.so
popd

%if %{with_zts}
pushd %{pecl_name}-%{version}-zts
TEST_PHP_EXECUTABLE=$(which zts-php) zts-php run-tests.php \
    -n -q -d extension_dir=modules \
    -d extension=apcu.so
popd
%endif


%if 0%{?pecl_install:1}
%post
%{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
%endif


%if 0%{?pecl_uninstall:1}
%postun
if [ $1 -eq 0 ] ; then
    %{pecl_uninstall} %{pecl_name} >/dev/null || :
fi
%endif


%clean
%{__rm} -rf %{buildroot}


%files
%defattr(-, root, root, 0755)
%doc %{pecl_name}-%{version}/{TECHNOTES.txt,LICENSE,NOTICE,apc.php,INSTALL}
%config(noreplace) %{php_inidir}/apcu.ini
%{php_extdir}/apcu.so
%{pecl_xmldir}/%{name}.xml

%if %{with_zts}
%config(noreplace) %{php_ztsinidir}/apcu.ini
%{php_ztsextdir}/apcu.so
%endif

%files devel
%defattr(-,root,root,-)
%{php_incldir}/ext/%{pecl_name}
%{php_ztsincldir}/ext/%{pecl_name}

%changelog
* Sat Sep 16 2017 Andy Thompson <andy@webtatic.com> - 5.1.8-2
- rebuild for EL7.4

* Sat Jun 24 2017 Andy Thompson <andy@webtatic.com> - 5.1.8-1.1
- Rebuild for php-7.2.0alpha2 Zend ABI version change

* Sun Apr 23 2017 Andy Thompson <andy@webtatic.com> - 5.1.8-1
- Update to APCu 5.1.8

* Sat Oct 22 2016 Andy Thompson <andy@webtatic.com> - 5.1.7-1
- Update to APCu 5.1.7

* Fri Oct 07 2016 Andy Thompson <andy@webtatic.com> - 5.1.6-1
- Update to APCu 5.1.6

* Tue Jun 21 2016 Andy Thompson <andy@webtatic.com> - 5.1.5-1
- Update to APCu 5.1.5

* Sat Jan 16 2016 Andy Thompson <andy@webtatic.com> - 5.1.3-1
- Update to APCu 5.1.3

* Sun Jan 10 2016 Andy Thompson <andy@webtatic.com> - 5.1.2-1
- branch from php5-pecl-apc
- Update to APCu 5.1.2
