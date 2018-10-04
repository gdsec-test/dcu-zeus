from distutils.core import setup

from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=False)
testing_reqs = parse_requirements('test_requirements.txt', session=False)

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]
test_reqs = [str(ir.req) for ir in testing_reqs]

setup(name='zeus',
      version='1.0',
      description='Deals with automated action of abuse reports',
      author='DCU',
      author_email='dcueng@godaddy.com',
      url='https://github.secureserver.net/nlemay/zeus',
      package_dir={'zeus': 'zeus'},
      packages=['zeus', 'zeus.events', 'zeus.events.email', 'zeus.events.support_tools', 'zeus.events.suspension',
                'zeus.events.user_logging', 'zeus.handlers', 'zeus.persist', 'zeus.reviews', 'zeus.utils'],
      include_package_data=True,
      install_requires=reqs,
      tests_require=test_reqs,
      test_suite="nose.collector")
