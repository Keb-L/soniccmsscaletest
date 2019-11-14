#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, shutil, logging, subprocess
import os.path as osp
import soniccmsscaletest
logger = logging.getLogger('soniccmsscaletest')
subprocess_logger = logging.getLogger('subprocess')

def _create_directory_no_checks(dirname, dry=False):
    """
    Creates a directory without doing any further checks, and logs.

    :param dirname: Name of the directory to be created
    :type dirname: str
    :param dry: Don't actually create the directory, only log
    :type dry: bool, optional
    """
    logger.warning('Creating directory {0}'.format(dirname))
    if not dry: os.makedirs(dirname)

def create_directory(dirname, force=False, must_not_exist=False, dry=False):
    """
    Creates a directory if certain conditions are met.

    :param dirname: Name of the directory to be created
    :type dirname: str
    :param force: Removes the directory `dirname` if it already exists
    :type force: bool, optional
    :param must_not_exist: Throw an OSError if the directory already exists
    :type must_not_exist: bool, optional
    :param dry: Don't actually create the directory, only log
    :type dry: bool, optional
    """
    if osp.isfile(dirname):
        raise OSError('{0} is a file'.format(dirname))
    isdir = osp.isdir(dirname)

    if isdir:
        if must_not_exist:
            raise OSError('{0} must not exist but exists'.format(dirname))
        elif force:
            logger.warning('Deleting directory {0}'.format(dirname))
            if not dry: shutil.rmtree(dirname)
        else:
            logger.warning('{0} already exists, not recreating')
            return
    _create_directory_no_checks(dirname, dry=dry)

class switchdir(object):
    """
    Context manager to temporarily change the working directory.

    :param newdir: Directory to change into
    :type newdir: str
    :param dry: Don't actually change directory if set to True
    :type dry: bool, optional
    """
    def __init__(self, newdir, dry=False):
        super(switchdir, self).__init__()
        self.newdir = newdir
        self._backdir = os.getcwd()
        self._no_need_to_change = (self.newdir == self._backdir)
        self.dry = dry

    def __enter__(self):
        if self._no_need_to_change:
            logger.info('Already in right directory, no need to change')
            return
        logger.info('chdir to {0}'.format(self.newdir))
        if not self.dry: os.chdir(self.newdir)

    def __exit__(self, type, value, traceback):
        if self._no_need_to_change:
            return
        logger.info('chdir back to {0}'.format(self._backdir))
        if not self.dry: os.chdir(self._backdir)

def run_command(cmd, env=None, dry=False, shell=False):
    logger.warning('Issuing command: {0}'.format(' '.join(cmd)))
    if dry: return
    if shell:
        cmd = ' '.join(cmd)
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        universal_newlines=True,
        shell=shell
        )
    for stdout_line in iter(process.stdout.readline, ""):
        subprocess_logger.info(stdout_line.rstrip('\n'))
    process.stdout.close()
    process.wait()
    returncode = process.returncode

    if returncode == 0:
        logger.info('Command exited with status 0 - all good')
    else:
        logger.error('Exit status {0} for command: {1}'.format(returncode, cmd))
        raise subprocess.CalledProcessError(cmd, returncode)

def run_multiple_commands(cmds, env=None, dry=False):
    if dry:
        logger.info('Sending:\n{0}'.format(pprint.pformat(cmds)))
        return
    process = subprocess.Popen(
        'bash',
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        # universal_newlines=True,
        bufsize=1,
        close_fds=True
        )
    # Break on first error (stdin will still be written but execution will be stopped)
    process.stdin.write('set -e\n')
    process.stdin.flush()
    for cmd in cmds:
        if not(type(cmd) is str):
            cmd = ' '.join(cmd)
        if not(cmd.endswith('\n')):
            cmd += '\n'
        logger.warning('Sending cmd \'{0}\''.format(cmd.replace('\n', '\\n')))
        process.stdin.write(cmd)
        process.stdin.flush()
    process.stdin.close()
    process.stdout.flush()
    for line in iter(process.stdout.readline, ""):
        if len(line) == 0: break
        # print(colored('[subprocess] ', 'red') + line, end='')
        subprocess_logger.info(line.rstrip('\n'))

    process.stdout.close()
    process.wait()
    returncode = process.returncode
    if (returncode == 0):
        logger.info('Command exited with status 0 - all good')
    else:
        raise subprocess.CalledProcessError(cmd, returncode)

def check_is_cmssw_path(path):
    assert osp.basename(path).startswith('CMSSW')
    assert osp.isdir(osp.join(path, 'src'))


def tarball_head(outfile=None):
    """
    Creates a tarball of the latest commit
    """
    if outfile is None:
        outfile = osp.join(os.getcwd(), 'soniccmsscaletest.tar')
    outfile = osp.abspath(outfile)

    with switchdir(osp.join(osp.dirname(osp.abspath(__file__)), '..')):
        run_command(['git', 'archive', '-o', outfile, 'HEAD'])

