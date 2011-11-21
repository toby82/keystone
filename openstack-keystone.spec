
#
# This is stable/diablo 2011-11-09 snapshot
#
%global milestone e2
%global git_revno 1262
%global snapdate 20111118
%global snaptag ~%{milestone}~%{snapdate}.%{git_revno}

Name:           openstack-keystone
Version:        2011.3.1
Release:        1%{?dist}
Summary:        OpenStack Identity Service

License:        ASL 2.0
URL:            http://keystone.openstack.org/
Source0:        http://keystone.openstack.org/tarballs/keystone-%{version}%{snaptag}.tar.gz
Source1:        openstack-keystone.logrotate
Source2:        openstack-keystone.service

BuildArch:      noarch
BuildRequires:  python2-devel
BuildRequires:  python-sphinx >= 1.0
BuildRequires:  python-iniparse
BuildRequires:  systemd-units

Requires:       python-eventlet
Requires:       python-httplib2
Requires:       python-ldap
Requires:       python-lxml
Requires:       python-memcached
Requires:       python-paste
Requires:       python-paste-deploy
Requires:       python-paste-script
Requires:       python-routes
Requires:       python-sqlalchemy
Requires:       python-sqlite2
Requires:       python-webob
Requires:	python-passlib

Requires(post):   systemd-units
Requires(preun):  systemd-units
Requires(postun): systemd-units
Requires(postun): python-iniparse
Requires(pre):    shadow-utils

%description
Keystone is a proposed independent authentication service for
OpenStack (http://www.openstack.org).

This initial proof of concept aims to address the current use cases in
Swift and Nova which are:

* REST-based, token auth for Swift
* many-to-many relationship between identity and tenant for Nova.


%prep
%setup -q -n keystone-%{version}

# log_file is ignored, use log_dir instead
# https://bugs.launchpad.net/keystone/+bug/844959/comments/3
python -c 'import iniparse
conf=iniparse.ConfigParser()
conf.read("etc/keystone.conf")
if conf.has_option("DEFAULT", "log_file"):
    conf.remove_option("DEFAULT", "log_file")
conf.set("DEFAULT", "log_dir", "%{_localstatedir}/log/keystone")
conf.set("keystone.backends.sqlalchemy", "sql_connection", "sqlite:///%{_sharedstatedir}/keystone/keystone.sqlite")
fp=open("etc/keystone.conf","w")
conf.write(fp)
fp.close()'

find . \( -name .gitignore -o -name .placeholder \) -delete
find keystone -name \*.py -exec sed -i '/\/usr\/bin\/env python/d' {} \;


%build
%{__python} setup.py build
find examples -type f -exec chmod 0664 \{\} \;

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

install -p -D -m 644 etc/keystone.conf %{buildroot}%{_sysconfdir}/keystone/keystone.conf
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-keystone
install -p -D -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/openstack-keystone.service
install -d -m 755 %{buildroot}%{_sharedstatedir}/keystone
install -d -m 755 %{buildroot}%{_localstatedir}/log/keystone

rm -rf %{buildroot}%{python_sitelib}/tools
rm -rf %{buildroot}%{python_sitelib}/examples
rm -rf %{buildroot}%{python_sitelib}/doc

# docs generation requires everything to be installed first
export PYTHONPATH="$( pwd ):$PYTHONPATH"
pushd doc
make
popd
# Fix hidden-file-or-dir warnings
rm -fr doc/build/html/.doctrees doc/build/html/.buildinfo

%pre
getent group keystone >/dev/null || groupadd -r keystone
getent passwd keystone >/dev/null || \
useradd -r -g keystone -d %{_sharedstatedir}/keystone -s /sbin/nologin \
-c "OpenStack Keystone Daemons" keystone
exit 0

%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable openstack-keystone.service > /dev/null 2>&1 || :
    /bin/systemctl stop openstack-keystone.service > /dev/null 2>&1 || :
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    # fix conf for LP844959
    python -c 'import iniparse
conf_file="%{_sysconfdir}/keystone/keystone.conf"
conf=iniparse.ConfigParser()
conf.read(conf_file)
if not conf.has_option("DEFAULT", "log_dir"):
    conf.set("DEFAULT", "log_dir", "%{_localstatedir}/log/keystone")
    fp=open(conf_file,"w")
    conf.write(fp)
    fp.close()'
    /bin/systemctl try-restart openstack-keystone.service >/dev/null 2>&1 || :
fi

%files
%doc README.md
%doc doc/build/html
%doc examples
%{python_sitelib}/*
%{_bindir}/keystone*
%{_unitdir}/openstack-keystone.service
%dir %{_sysconfdir}/keystone
%config(noreplace) %{_sysconfdir}/keystone/keystone.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/openstack-keystone
%dir %attr(-, keystone, keystone) %{_sharedstatedir}/keystone
%dir %attr(-, keystone, keystone) %{_localstatedir}/log/keystone

%changelog
* Mon Nov 21 2011 Alan Pevec <apevec@redhat.com> 2011.3.1-1
- Update to 2011.13.1 stable/diablo release

* Fri Nov 11 2011 Alan Pevec <apevec@redhat.com> 2011.3-2
- Update to the latest stable/diablo snapshot

* Mon Oct 24 2011 Mark McLoughlin <markmc@redhat.com> - 2011.3-1
- Update version to diablo final

* Wed Oct 19 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.4.d4.1213
- add Requires: python-passlib

* Mon Oct 3 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.2.d4.1213
- update to diablo release.
- BR systemd-units for _unitdir

* Fri Sep  2 2011 Mark McLoughlin <markmc@redhat.com> - 1.0-0.2.d4.1078
- Use upstream snapshot tarball
- No need to define python_sitelib anymore
- BR python2-devel
- Remove BRs only needed for unit tests
- No need to clean buildroot in install anymore
- Use slightly more canonical site for URL tag
- Prettify the requires tags
- Cherry-pick tools.tracer patch from upstream
- Add config file
- Add keystone user and group
- Ensure log file is in /var/log/keystone
- Ensure the sqlite db is in /var/lib/keystone
- Add logrotate support
- Add system units

* Thu Sep  1 2011 Matt Domsch <Matt_Domsch@dell.com> - 1.0-0.1.20110901git396f0bfd%{?dist}
- initial packaging
