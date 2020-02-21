#!/usr/bin/env python
# -*- coding: utf-8 -*-
import soniccmsscaletest
import os.path as osp
from time import sleep
import logging, datetime, os, glob
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
        self.datafile = osp.abspath(datafile)
        self.cmssw_path = osp.abspath(cmssw_path)
        self.arch = 'slc7_amd64_gcc700'
        self.dry = dry
        soniccmsscaletest.utils.check_is_cmssw_path(self.cmssw_path)


    def run_at_time(self, time, late_tolerance_min=5, n_events=None, apply_lpcwn_offset=True):
        """
        :param time: Date string with format self.date_fmt_str. time should be in the 
        future; it is allowed to be late by late_tolerance_min minutes
        :type time: str
        :param late_tolerance_min: Amount of minutes the job can be late and still start
        :type late_tolerance_min: str
        """

        self.prepare()

        def get_now():
            now = datetime.datetime.now()
            if apply_lpcwn_offset:
                logger.warning('Applying WN offset of 6 hours!')
                now -= datetime.timedelta(hours=6)
            return now

        run_time = datetime.datetime.strptime(time, self.date_fmt_str)
        now = get_now()
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

        logger.info('Starting run at {0}'.format(get_now().strftime(self.date_fmt_str)))
        self.run(n_events)

    def prepare(self):
        cmds = [
            'shopt -s expand_aliases','uname -r',
            'source /cvmfs/cms.cern.ch/cmsset_default.sh',
            'cd {0}/src'.format(self.cmssw_path),
            'scram b ProjectRename',
            'scram b ExternalLinks',
            'cmsenv',
            'export SCRAM_ARCH={0}'.format(self.arch),
            'cd SonicCMS/TensorRT/python',
            'xrdcp root://eoscms.cern.ch//store/data/Run2018A/HLTPhysics/RAW/v1/000/316/944/00000/E266D611-7E61-E811-B73D-FA163E84650C.root .'
        ]
        soniccmsscaletest.utils.run_multiple_commands(cmds)
         
    def run(self, n_events=None):
        n_events = self.n_events if n_events is None else n_events
        cmds = [
            'shopt -s expand_aliases','uname -r',
            'source /cvmfs/cms.cern.ch/cmsset_default.sh',
            'cd {0}/src'.format(self.cmssw_path),
            'scram b ProjectRename',
            'scram b ExternalLinks',
            'cmsenv',
            'export SCRAM_ARCH={0}'.format(self.arch),
            'cd SonicCMS/TensorRT/python',
            [
                'cmsRun OnLine_HLT_GRun.py'
                #'maxEvents={0}'.format(n_events),
                #'address={0}'.format(self.address),
                #'port={0}'.format(self.port),
                #'datafile={0}'.format(self.datafile)
                ]
            ]
        env = os.environ.copy()
        del env['PATH']
        del env['PYTHONPATH']
        soniccmsscaletest.utils.run_multiple_commands(cmds)


    def concatenate_output(self, outfile=None):
        if outfile is None: outfile = 'concat_outputs.txt'
        outputs = glob.glob(osp.join(self.cmssw_path, 'src/SonicCMS/TensorRT/python', 'output*.txt'))
        concatenated = ''
        for output in outputs:
            concatenated += '<output>\n'
            concatenated += 'file: {0}\n'.format(osp.basename(output))
            with open(output, 'r') as f:
                concatenated += f.read()
            concatenated += '</output>\n'
        logger.warning('Writing concatenated outputs to {0}'.format(outfile))
        with open(outfile, 'w') as f:
            f.write(concatenated)


