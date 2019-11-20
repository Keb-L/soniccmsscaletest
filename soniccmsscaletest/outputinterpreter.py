#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import soniccmsscaletest
import os.path as osp
from time import sleep
import logging, datetime, os, glob, re, pprint, math
logger = logging.getLogger('soniccmsscaletest')

# <output>
# file: output_3252.txt
# starttime: Mon Nov 18 17:28:31 2019
# remoteduration: 230604 microseconds
# Convert succeeded.
# scores: [0.00222227 0.99777776]
# string: classifier/model_1/classifier_output/Softmax:0
# </output>
# <output>

date_fmt_str_in_output = '%a %b %d %H:%M:%S %Y'
short_date_fmt_str = '%H:%M:%S:%f'


def timedelta_to_seconds(td):
    """
    For compatibility with Python 2.6
    """
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / float(10**6)


class OutputInterpreter(object):
    """
    OutputInterpreter docstring

    :param variable: Description of some variable
    :type variable: str, optional
    """

    def __init__(self):
        """
        Constructor method
        """
        super(OutputInterpreter, self).__init__()
        self.arch = soniccmsscaletest.SCRAM_ARCH
        self.date_fmt_str = soniccmsscaletest.DATE_FMT_STR

    def read_output_file(self, output_file):
        logger.info('Reading output from {0}'.format(output_file))
        with open(output_file, 'r') as f:
            contents = f.read()
        inferences = []
        for raw in contents.split('</output>'):
            raw = raw.strip('<output>\n').strip()
            if len(raw) == 0: continue
            # logger.debug('Raw output:\n{0}'.format(raw))
            inf = Inference.from_raw_output_str(raw, src_file=osp.basename(output_file))
            inferences.append(inf)
        logger.info('Determined {0} inferences from file {1}'.format(len(inferences), output_file))
        return inferences

    def interpret(self, output_files):
        all_inferences = []
        output_per_file = {}
        for file in output_files:
            inferences = self.read_output_file(file)
            output_per_file[osp.basename(file)] = Output(osp.basename(file), inferences)
            all_inferences.extend(inferences)
        combined_output = Output('all', all_inferences)
        return combined_output, output_per_file


class Output(object):
    """docstring for Output"""
    def __init__(self, name, inferences):
        super(Output, self).__init__()
        self.name = name
        self.inferences = inferences
        self.inferences_by_end_time = None
        self.inferences_by_start_time = None

    def sort_inferences_by_end_time(self):
        if not(self.inferences_by_end_time):
            self.inferences_by_end_time = list(sorted(self.inferences, key=lambda inf: inf.end_time))
        return self.inferences_by_end_time

    def sort_inferences_by_start_time(self):
        if not(self.inferences_by_start_time):
            self.inferences_by_start_time = list(sorted(self.inferences, key=lambda inf: inf.start_time))
        return self.inferences_by_start_time

    def get_earliest_start_time(self):
        inferences = self.sort_inferences_by_start_time()
        return inferences[0].start_time

    def get_latest_end_time(self):
        inferences = self.sort_inferences_by_end_time()
        return inferences[-1].end_time

    def bin_inferences(self, bin_width=datetime.timedelta(minutes=1), start_time=None, end_time=None):
        if start_time is None: start_time = self.get_earliest_start_time()
        if end_time is None: end_time = self.get_latest_end_time()
        # Calculate number of bins given the specified bin_width
        total_duration = end_time - start_time

        logger.debug('total_duration: {0}'.format(timedelta_to_seconds(total_duration)))

        n_bins = int(math.ceil(timedelta_to_seconds(total_duration) / timedelta_to_seconds(bin_width)))
        # Create a binning
        logger.info(
            'Creating {0} bins (width = {1:.4f}s) between {2} and {3}'
            .format(
                n_bins, timedelta_to_seconds(bin_width),
                start_time.strftime(short_date_fmt_str),
                end_time.strftime(short_date_fmt_str),
                )
            )
        binning = [ Bin(start_time+i*bin_width, start_time+(i+1)*bin_width) for i in range(n_bins) ]
        # Function to conveniently find the right bin for a given inference
        def find_bin(inference):
            for i, b in enumerate(binning):
                # if inference.end_time < b.right and inference.start_time >= b.left:
                #     return b
                if b.right > inference.end_time:
                    return b
            else:
                logger.error('No bin found for:\n{0}'.format(inference))
        for inf in self.inferences_by_start_time:
            find_bin(inf).inferences.append(inf)
        return binning


class Bin(Output):
    """
    Like the Output container, but has a left and right bin boundary,
    does not have a meaningful name, and starts empty
    """

    def __init__(self, left, right):
        super(Bin, self).__init__('timebin', [])
        self.left = left
        self.right = right

    def __repr__(self):
        return (
            '[ {0} to {1} ): {2} inferences'
            .format(
                self.left.strftime(short_date_fmt_str),
                self.right.strftime(short_date_fmt_str),
                len(self.inferences)
                )
            )


class Inference(object):
    """Represents one inference"""

    @classmethod
    def from_raw_output_str(cls, raw, src_file=None):
        file = 'unknown'
        event_number = -1
        start_time = None
        remote_duration = None
        scores = []
        success = False
        split_semicolon = lambda line: line.split(':', 1)[1].strip()
        lines = raw.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue
            elif line.startswith('file:'):
                file = split_semicolon(line)
                match = re.match(r'output_(\d+)\.txt', file)
                if match:
                    event_number = int(match.group(1))
            elif line.startswith('starttime:'):
                start_time = datetime.datetime.strptime(
                    split_semicolon(line),
                    date_fmt_str_in_output
                    )
            elif line.startswith('remoteduration:'):
                remote_duration = int(split_semicolon(line).split(' ')[0])
            elif line.startswith('scores:'):
                scores = [ float(i) for i in split_semicolon(line).strip('[]').split() ]
            elif line.startswith('Convert succeeded'):
                success = True

        if not(start_time) or not(remote_duration):
            raise ValueError(
                'The following raw output string could not be interpreted:\n{0}'
                .format(raw)
                )

        return cls(
            start_time = start_time, remote_duration = remote_duration,
            file = file, event_number = event_number, scores = scores, success = success,
            src_file = src_file
            )

    def __init__(self, start_time, remote_duration, **kwargs):
        super(Inference, self).__init__()
        self.start_time = start_time
        self.remote_duration = remote_duration
        self.end_time = start_time + datetime.timedelta(microseconds=remote_duration)
        self.attrs = kwargs

    def __repr__(self):
        return (
            '{0} --> {1:7.2f} ms --> {2}\n  {3}'
            .format(
                self.start_time.strftime(short_date_fmt_str),
                self.remote_duration / 1000.,
                self.end_time.strftime(short_date_fmt_str),
                pprint.pformat(self.attrs)
                )
            )




