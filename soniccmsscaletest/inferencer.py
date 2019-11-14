#!/usr/bin/env python
# -*- coding: utf-8 -*-
import soniccmsscaletest
import os.path as osp
from time import sleep
import logging, datetime, os
logger = logging.getLogger('soniccmsscaletest')

class Inferencer(object):
    """
    Inferencer docstring

    :param variable: Description of some variable
    :type variable: str, optional
    """

    date_fmt_str = '%Y-%m-%d %H:%M:%S'

    @classmethod
    def from_tarball(cls, address, port, n_events, datafile, tarball, outdir, dry=False):
        cmssw_path = soniccmsscaletest.TarballManager().extract_tarball(tarball, outdir=outdir, dry=dry)
        return cls(address, port, n_events, datafile, cmssw_path, dry=dry)

    def __init__(self, address, port, n_events, datafile, cmssw_path, dry=False):
        """
        Constructor method
        """
        super(Inferencer, self).__init__()
        self.address = address
        self.port = port
        self.n_events = n_events
        self.datafile = datafile
        self.cmssw_path = osp.abspath(cmssw_path)
        self.arch = 'slc6_amd64_gcc700'
        self.dry = dry
        soniccmsscaletest.utils.check_is_cmssw_path(self.cmssw_path)


    def run_at_time(self, time, late_tolerance_min=5, n_events=None):
        """
        :param time: Date string with format self.date_fmt_str. time should be in the 
        future; it is allowed to be late by late_tolerance_min minutes
        :type time: str
        :param late_tolerance_min: Amount of minutes the job can be late and still start
        :type late_tolerance_min: str
        """
        run_time = datetime.datetime.strptime(time, self.date_fmt_str)
        now = datetime.datetime.now()
        delta = run_time - now
        negative_delta = now - run_time
        delta_tolerance = datetime.timedelta(minutes=late_tolerance_min)

        logger.info('Current time:       {0}'.format(now.strftime(self.date_fmt_str)))
        logger.info('Scheduled run time: {0}'.format(run_time.strftime(self.date_fmt_str)))

        if negative_delta > datetime.timedelta(minutes=0):
            logger.warning('Job is late by {0} minutes'.format(negative_delta.seconds/60.))
            if negative_delta < delta_tolerance:
                logger.info('Less than {0} minutes late, so starting immediately'.format(late_tolerance_min))
            else:
                logger.info('Past late tolerance ({0} min), aborting'.format(late_tolerance_min))
                return 1
        else:
            logger.warning('Job is early by {0} minutes; sleeping {1} seconds'.format(delta.seconds/60., delta.seconds))
            sleep(delta.seconds)

        logger.info('Starting run at {0}'.format(datetime.datetime.now().strftime(self.date_fmt_str)))
        self.run(n_events)

    def run(self, n_events=None):
        n_events = self.n_events if n_events is None else n_events
        cmds = [
            'shopt -s expand_aliases',
            'source /cvmfs/cms.cern.ch/cmsset_default.sh',
            'export SCRAM_ARCH={0}'.format(self.arch),
            'cd {0}/src'.format(self.cmssw_path),
            'scram b ProjectRename',
            'cmsenv',
            'cd SonicCMS/AnalysisFW/python',
            [
                'cmsRun jetImageTest_mc_cfg.py',
                'maxEvents={0}'.format(n_events),
                'address={0}'.format(self.address),
                'port={0}'.format(self.port),
                'datafile={0}'.format(self.datafile)
                ]
            ]
        env = os.environ.copy()
        del env['PATH']
        del env['PYTHONPATH']
        soniccmsscaletest.utils.run_multiple_commands(cmds)





