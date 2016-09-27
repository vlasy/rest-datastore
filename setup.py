import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand


def get_long_description():
    with open('README.md') as f:
        rv = f.read()
    return rv


def get_requirements(suffix=''):
    with open('requirements%s.txt' % suffix) as f:
        rv = f.read().splitlines()
    return rv


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [
            '--cov', 'rest_datastore',
            '--cov-report', 'term-missing',
            '--pep8',
            '--flakes',
            '--cache-clear'
        ]
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name='REST-Datastore',
    version='1.0.0',
    url='https://github.com/vlasy/rest-datastore',
    license='MIT',
    author='vlasy',
    description='REST datastore for Flask-Security',
    long_description=get_long_description(),
    install_requires=get_requirements(),
    tests_require=get_requirements('-dev'),
    cmdclass={'test': PyTest},
)
