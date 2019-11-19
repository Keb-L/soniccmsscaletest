from setuptools import setup

setup(
    name          = 'soniccmsscaletest',
    version       = '0.1',
    license       = 'BSD 3-Clause License',
    description   = 'Description text',
    url           = 'https://github.com/tklijnsma/soniccmsscaletest.git',
    download_url  = 'https://github.com/tklijnsma/soniccmsscaletest/archive/v0_1.tar.gz',
    author        = 'Thomas Klijnsma',
    author_email  = 'tklijnsm@gmail.com',
    packages      = ['soniccmsscaletest'],
    zip_safe      = False,
    tests_require = ['nose'],
    test_suite    = 'nose.collector',
    scripts       = [
        'bin/soniccmsscaletest-run',
        'bin/soniccmsscaletest-maketarball',
        'bin/soniccmsscaletest-runtarball',
        'bin/soniccmsscaletest-submitscaletest',
        'bin/soniccmsscaletest-interpret',
        ],
    )
