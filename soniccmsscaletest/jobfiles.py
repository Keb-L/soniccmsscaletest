#!/usr/bin/env python
# -*- coding: utf-8 -*-
import soniccmsscaletest
import os.path as osp
from time import sleep
import logging, datetime, os, collections
logger = logging.getLogger('soniccmsscaletest')

echo = lambda text: 'echo "{0}"'.format(text.replace('"', '\\"'))

class File(object):
    """docstring for File"""
    def __init__(self):
        super(File, self).__init__()

    def parse(self):
        return ''

    def _write_nochecks(self, filename):
        with open(filename, 'w') as f:
            logger.info('Writing contents to {0}'.format(filename))
            f.write(self.parse())
        
    def write(self, filename, must_not_exist=False, dry=False):
        if osp.isfile(filename):
            if must_not_exist:
                raise OSError('File {0} already exists but must not exist'.format(filename))
            else:
                logger.warning('Overwriting {0}'.format(filename))
        if not dry:
            self._write_nochecks(filename)


class JDLBase(File):
    """docstring for JDLBase"""
    def __init__(self):
        super(JDLBase, self).__init__()
        
    def __init__(self):
        super(JDLBase, self).__init__()
        self.environment = {
            'SCRAM_ARCH': soniccmsscaletest.SCRAM_ARCH,
            'CONDOR_CLUSTER_NUMBER' : '$(Cluster)',
            'CONDOR_PROCESS_ID' : '$(Process)',
            'USER' : os.environ['USER'],
            }
        self.options = collections.OrderedDict()
        self.options['universe'] = 'vanilla'
        self.options['environment'] = self.environment
        self.queue = 'queue'

    def subparse(self):
        pass

    def parse(self):
        self.subparse()
        jdl = []
        for key, value in self.options.items():
            if key == 'environment':
                jdl.append('environment = "{0}"'.format(self.parse_environment()))
            else:
                jdl.append('{0} = {1}'.format(key, value))
        jdl.append(self.queue)
        jdl = '\n'.join(jdl)
        logger.info('Parsed the following jdl file:\n{0}'.format(jdl))
        return jdl

    def parse_environment(self):
        return ' '.join([ '{0}=\'{1}\''.format(key, value) for key, value in self.environment.items() ])


class JDLFile(JDLBase):
    """docstring for JDLFile"""

    starting_seed = 1001

    def __init__(self, sh_file, cmssw_tarball, datafile, n_jobs, name, runtime=None, soniccmsscaletest_tarball=None):
        super(JDLFile, self).__init__()
        self.sh_file = sh_file
        self.cmssw_tarball = cmssw_tarball
        self.datafile = datafile
        self.n_jobs = n_jobs
        self.soniccmsscaletest_tarball = soniccmsscaletest_tarball
        self.runtime = runtime
        self.name = name 
    def subparse(self):
        self.options['executable'] = self.sh_file
        self.options['should_transfer_files'] = 'YES'  # May not be needed if staging out to SE!
        self.options['when_to_transfer_output'] = 'ON_EXIT'
        self.options['transfer_output_files'] = 'output'  # Just transfer a dir caled 'output'
        self.options['transfer_input_files'] = [ self.cmssw_tarball, self.datafile ]
        if self.soniccmsscaletest_tarball:
            logger.info('Added {0} to input files'.format(self.soniccmsscaletest_tarball))
            self.options['transfer_input_files'].append(self.soniccmsscaletest_tarball)
        self.options['transfer_input_files'] = ','.join(self.options['transfer_input_files'])
        self.options['notification'] = 'Complete'
        self.options['notify_user'] = 'jeffkrupa@gmail.com'
        self.options['output'] = 'sonic_$(Cluster)_$(Process)_%i.stdout'%self.n_jobs
        self.options['error']  = 'sonic_$(Cluster)_$(Process)_%i.stderr'%self.n_jobs
        self.options['log']    = 'sonic_$(Cluster)_$(Process)_%i.log'%self.n_jobs
        self.options['+REQUIRED_OS'] = '"rhel7"'
        self.options['x509userproxy'] = '/uscms/home/jkrupa/nobackup/x509up_jk'
        self.options['RequestMemory'] = '6000'#'/uscms/home/jkrupa/nobackup/x509up_jk'
        # Make sure of time at which to run
        if self.runtime:
            datetime.datetime.strptime(self.runtime, '%Y-%m-%d %H:%M:%S')  # Make sure str has right format
            self.environment['runtime'] = self.runtime
        # Queue one job per seed
        seeds = [ str(self.starting_seed + i) for i in range(self.n_jobs) ]
        self.queue = 'queue 1 arguments in {0}'.format(', '.join(seeds))


class SHFile(File):
    """docstring for SHFile"""
    def __init__(self,
        cmssw_tarball,
        address,
        port,
        nevents,
        datafile,
        runtime=None,
        soniccmsscaletest_tarball=None
        ): 
        super(SHFile, self).__init__()
        # Files will be basenames on the node
        self.cmssw_tarball = osp.basename(cmssw_tarball)
        self.datafile = osp.basename(datafile)
        self.soniccmsscaletest_tarball = osp.basename(soniccmsscaletest_tarball) if soniccmsscaletest_tarball else None
        self.runtime = runtime
        # Inferencing client parameters
        self.address = address
        self.port = port
        self.nevents = nevents

    def get_soniccmsscaletest_pkg(self):
        if self.soniccmsscaletest_tarball:
            logger.info('soniccmsscaletest_tarball was passed; will extract')
            return [
                echo('Extracting soniccmsscaletest_tarball'),
                'mkdir soniccmsscaletest',
                'tar xf soniccmsscaletest.tar -C soniccmsscaletest/',
                'export PATH="${PWD}/soniccmsscaletest/bin:${PATH}"',
                'export PYTHONPATH="${PWD}/soniccmsscaletest:${PYTHONPATH}"',
                ]
        else:
            raise NotImplementedError('TODO')


    def parse(self):
        sh = [
            '#!/bin/bash',
            'set -e',
            echo('##### HOST DETAILS #####'),
            echo('hostname: $(hostname)'),
            echo('date:     $(date)'),
            echo('pwd:      $(pwd)'),
            'export SEED=$1',
            echo('seed:     ${SEED}'),
            ]
        sh.extend(self.get_soniccmsscaletest_pkg())
        cmd = (
            'soniccmsscaletest-runtarball {tarball} '
            '{runtime_opt} -a {address} -p {port} -n {nevents} -d {datafile} '
            '--output "output/concat_output_${{CONDOR_PROCESS_ID}}.txt"'
            .format(
                tarball = self.cmssw_tarball,
                runtime_opt = '--runtime "{0}"'.format(self.runtime) if self.runtime else '',
                address = self.address,
                port = self.port,
                nevents = self.nevents,
                datafile = self.datafile,
                )
            )
        sh.extend([
            'mkdir output',
            echo('ls -al:'),
            'ls -al',
            echo('Running: {0}'.format(cmd)),
            cmd
            ])
        contents = '\n'.join(sh)
        logger.debug('Parsed sh file:\n{0}'.format(contents))
        return contents

