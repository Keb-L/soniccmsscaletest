#!/usr/bin/env python
# -*- coding: utf-8 -*-
import soniccmsscaletest
import os.path as osp
import logging, glob
logger = logging.getLogger('soniccmsscaletest')

class TarballManager(object):
    """
    TarballManager docstring
    """
    def __init__(self):
        """
        Constructor method
        """
        super(TarballManager, self).__init__()

    def make_tarball(self, cmssw_path, outdir='.', tag=None, dry=False):
        """
        :param cmssw_path: Path to CMSSW_BASE (i.e. ../src)
        :type cmssw_path: str
        :param outdir: Path to put the tarball. Defaults to cwd.
        :type outdir: str
        """
        cmssw_path = osp.abspath(cmssw_path)
        outdir = osp.abspath(outdir)
        soniccmsscaletest.utils.check_is_cmssw_path(cmssw_path)
        dst = osp.basename(cmssw_path).strip('/') + ('' if tag is None else '_' + tag) + '.tar.gz'
        dst_abs = osp.abspath(osp.join(outdir, dst))
        if osp.isfile(dst_abs): raise OSError('{0} already exists'.format(dst_abs))
        logger.warning(
            'Tarballing {0} ==> {1}'
            .format(osp.abspath(cmssw_path), dst_abs)
            )
        with soniccmsscaletest.utils.switchdir(osp.dirname(cmssw_path)):
            cmd = [
                'tar',
                '--exclude-caches-all',
                '--exclude-vcs',
                '-zcvf',
                # dst,
                dst_abs,
                osp.basename(cmssw_path),
                # '-C',
                # '--directory',
                # outdir,
                # '--exclude=src',  # Probably do need src... and it's anyway tiny
                '--exclude=tmp',
                ]
            soniccmsscaletest.utils.run_command(cmd, dry=dry)

    def extract_tarball(self, tarball, outdir='.', dry=False):
        tarball = osp.abspath(tarball)
        outdir = osp.abspath(outdir)
        logger.warning(
            'Extracting {0} ==> {1}'
            .format(tarball, outdir)
            )
        cmd = [
            'tar', '-xvf', tarball,
            '-C', outdir
            ]
        soniccmsscaletest.utils.run_command(cmd, dry=dry)
        # return the CMSSW directory
        if dry: return 'CMSSW_dry'
        return glob.glob(osp.join(outdir, 'CMSSW*'))[0]

