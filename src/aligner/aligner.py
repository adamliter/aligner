import os
import logging
import logging.config
import json
import pandas as pd
import numpy as np
from pydub import AudioSegment


logger = logging.getLogger(__name__)


class Aligner:
    def __init__(self, transcribed_csv, data_dir,
                 mp3_dir, transcriptions_dir, gentle_dir):
        self.logger = logger.getChild(self.__class__.__name__)
        self.transcribed_csv = transcribed_csv
        self.data_dir = data_dir
        self.mp3_dir = os.path.join(self.data_dir, mp3_dir)
        self.transcriptions_dir = os.path.join(
            self.data_dir, transcriptions_dir)
        self.gentle_dir = os.path.join(self.data_dir, gentle_dir)

        self.mp3_participants = [
            p for p in os.listdir(self.mp3_dir) if p != '.DS_Store']
        self.transcribed_participants = [
            p for p in os.listdir(self.transcriptions_dir) if p != '.DS_Store']

        try:
            assert self.mp3_participants == self.transcribed_participants
        except AssertionError:
            self.logger.error(
                'The participant directories for the .mp3 files and the '
                'participant directories for the transcription files do not '
                'match.')

        self.participants = self.mp3_participants

        self.longest_sent = None

    def align(self, overwrite=False, tg=True):
        for p in self.participants:
            self.logger.info('Force aligning audio for participant %(p)s' %
                             {'p': p})
            mp3_files = [
                f for f in os.listdir(os.path.join(self.mp3_dir, p))
                if '.mp3' in f]
            mp3_files.sort()

            transcription_files = [
                f for f in os.listdir(os.path.join(self.transcriptions_dir, p))
                if '.txt' in f]
            transcription_files.sort()

            gdir = os.path.join(self.gentle_dir, p)

            if not os.path.exists(gdir):
                os.makedirs(gdir)
                self.logger.info(
                    'Created directory:\n%(dir)s' % {'dir': gdir})

            for i, (m, t) in enumerate(zip(mp3_files, transcription_files)):
                align_file = os.path.join(gdir, str(i + 1).zfill(2) + '.json')
                with open(os.path.join(self.transcriptions_dir, p, t), 'r') \
                     as file_:
                    transcription = file_.read().strip().lower()
                # If the participant didn't say anything, the transcriber
                # was instructed to write 'empty' for the transcription
                if transcription == 'empty':
                    self.logger.warning(
                        'Participant %(p)s\'s recording for item %(i)s was '
                        'empty.' % {'p': p, 'i': i})
                    faux_gentle = {'transcript': '',
                                   'words': []}
                    with open(align_file, 'w') as file_:
                        json.dump(faux_gentle, file_, indent=2)
                else:
                    if os.path.exists(align_file) and overwrite:
                        self.logger.info(
                            'File, %(f)s, already exists. Overwriting.' %
                            {'f': align_file})

                    if os.path.exists(align_file) and not overwrite:
                        self.logger.info(
                            'File, %(f)s, already exists. Skipping.' %
                            {'f': align_file})

                    if overwrite or not os.path.isfile(align_file):
                        command = (
                            'curl -F "audio=@'
                            f'{os.path.join(self.mp3_dir, p, m)}" '
                            '-F "transcript=@'
                            f'{os.path.join(self.transcriptions_dir, p, t)}" '
                            '"http://localhost:8765/'
                            'transcriptions?async=false" '
                            f'> {align_file}')
                        self.logger.debug('Running shell command:\n%(c)s' %
                                          {'c': command})
                        os.system(command)

                if tg:
                    tgf = os.path.join(
                        self.mp3_dir, p,
                        'item_number_' + str(i + 1).zfill(2) + '.TextGrid')
                    self._write_textgrid_file(
                        os.path.join(self.mp3_dir, p, m), align_file, tgf)
                    self.logger.info('Wrote Praat TextGrid file:\n%(f)s' %
                                     {'f': tgf})

    def get_timing_info(self):
        df = pd.read_csv(self.transcribed_csv)
        self.longest_sent = max(
            np.vectorize(len)(
                np.char.split(df['Transcription'].unique().astype(str))))

        df = df.groupby('Participant', as_index=False).apply(
            lambda x: self._extract_timing_info(
                x, self.gentle_dir, self.longest_sent))

        df.to_csv(self.transcribed_csv, na_rep='NA', index=False)
        self.logger.info('Wrote file:\n%(f)s' % {'f': self.transcribed_csv})

    def _write_textgrid_file(self, mp3_file, json_file, textgrid_file):
        with open(json_file, 'r') as j:
            timing_info = json.load(j)

        transcription = timing_info['transcript']
        timing_info = timing_info['words']

        tg = ''
        num_intervals = 0

        # Only collect timing info for TextGrid file if transcription
        # is non-empty
        if transcription:
            aligner_successes = [x['case'] for x in timing_info]
            first_successful_word = aligner_successes.index('success')

            for i, word_info in enumerate(timing_info):
                if not word_info['case'] == 'success':
                    continue
                else:
                    num_intervals += 1
                    if i == first_successful_word:
                        xmin = 0
                        xmax = word_info['start']
                        text = '{SL}'

                        tg = self._append_tg_interval_to_str(
                            tg, num_intervals, xmin, xmax, text)

                        num_intervals += 1
                        xmin = word_info['start']
                        xmax = word_info['end']
                        text = word_info['alignedWord']

                        tg = self._append_tg_interval_to_str(
                            tg, num_intervals, xmin, xmax, text)

                        prev_offset = xmax
                    else:
                        xmin = word_info['start']
                        xmax = word_info['end']
                        text = word_info['alignedWord']

                        if xmin == prev_offset:
                            tg = self._append_tg_interval_to_str(
                                tg, num_intervals, xmin, xmax, text)
                        else:
                            tg = self._append_tg_interval_to_str(
                                tg, num_intervals, prev_offset, xmin, '')

                            num_intervals += 1

                            tg = self._append_tg_interval_to_str(
                                tg, num_intervals, xmin, xmax, text)

                        prev_offset = xmax

        xmin = 0
        mp3 = AudioSegment.from_file(mp3_file)
        xmax = mp3.duration_seconds

        with open(textgrid_file, 'w') as tgf:
            tgf.write('File type = "ooTextFile"\n')
            tgf.write('Object class = "TextGrid"\n\n')
            tgf.write(f'xmin = {xmin}\n')
            tgf.write(f'xmax = {xmax}\n')
            tgf.write('tiers? <exists>\n')
            tgf.write('size = 1\n')
            tgf.write('item []:\n')
            tgf.write('    item [1]:\n')
            tgf.write('        class = "IntervalTier"\n')
            tgf.write('        name = "word"\n')
            tgf.write(f'        xmin = {xmin}\n')
            tgf.write(f'        xmax = {xmax}\n')
            tgf.write(f'        intervals: size = {num_intervals}')
            if tg:
                tgf.write(tg)

    @staticmethod
    def _append_tg_interval_to_str(str_, interval, xmin, xmax, text):
        str_ += f'\n            intervals [{interval}]:'
        str_ += f'\n                xmin = {xmin}'
        str_ += f'\n                xmax = {xmax}'
        str_ += f'\n                text = "{text}"'
        return str_

    @staticmethod
    def _extract_timing_info(grp_df, gentle_dir, longest_sent):
        gentle_dir = os.path.join(
            gentle_dir, str(int(grp_df['Participant'].unique()[0])))
        json_files = [f for f in os.listdir(gentle_dir) if '.json' in f]
        json_files.sort()

        onset_cols = [f'Word{str(i + 1)}Onset' for i in range(longest_sent)]
        offset_cols = [f'Word{str(i + 1)}Offset' for i in range(longest_sent)]
        timing_cols = [
            val for pair in zip(onset_cols, offset_cols) for val in pair]

        timing_df = pd.DataFrame(
            np.empty((len(json_files), longest_sent * 2), dtype=np.float64),
            columns=timing_cols)
        timing_df[:] = np.nan

        for i, f in enumerate(json_files):
            with open(os.path.join(gentle_dir, f), 'r') as file_:
                timing_info = json.load(file_)
            timing_info = timing_info['words']

            for ii, word_info in enumerate(timing_info):
                if word_info['case'] == 'success':
                    timing_df.iloc[[i], [(ii * 2)]] = word_info['start']
                    timing_df.iloc[[i], [(ii * 2) + 1]] = word_info['end']
                else:
                    timing_df.iloc[[i], [(ii * 2)]] = float('inf')
                    timing_df.iloc[[i], [(ii * 2) + 1]] = float('inf')

        # If we've already run the script for at least 1 participant, then
        # the timing columns will also be present in the grp_df DataFrame
        # (though not all of them might be present, if there happens to be
        # a longer sentence in the new batch of data than was there before;
        # e.g., there might now be colums called Word15Onset and Word15Offset
        # whereas before there was only up to Word14Onset and Word14Offset)
        cols_to_drop = set(grp_df.filter(regex='Word.*Onset'))
        cols_to_drop.update(grp_df.filter(regex='Word.*Offset'))
        cols_to_drop.update(timing_cols)
        grp_df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
        grp_df.reset_index(drop=True, inplace=True)

        df = pd.concat([grp_df, timing_df], axis=1)

        return df


def main():
    import argparse
    from . import log_conf
    from .utils import set_class_log_level

    logging.config.dictConfig(log_conf)

    parser = argparse.ArgumentParser(
        description='Aligns transcriptions with audio files using the '
        'gentle forced aligner (https://lowerquality.com/gentle/), which'
        ' must be installed and running on port 8765 for this script to '
        'work as intended. The forced aligner writes .json files with '
        'timing information to data_dir/gentle_dir, and this timing info'
        ' is then extracted from those .json files and written back to the'
        ' main .csv file with all of the data.')

    parser.add_argument(
        '--file', '-f', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/'
        'data/exp1_data/ibex_results/exp1_data_tidy_transcribed.csv',
        help='Path to the .csv file with all of the information, including'
        ' the transcriptions.',
        dest='file_')

    parser.add_argument(
        '--data-dir', '-d', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/data/'
        'exp1_data',
        help='Path to the parent directory for all of the different data '
        'files.',
        dest='data_dir')

    parser.add_argument(
        '--mp3-dir', '-m', type=str,
        default='mp3_files',
        help='Relative path from data_dir to the directory with all of the'
        ' .mp3 files to be aligned with the transcriptions.',
        dest='mp3_dir')

    parser.add_argument(
        '--transcriptions-dir', '-t', type=str,
        default='transcriptions',
        help='Relative path from data_dir to the directory with all of the'
        ' transcriptions to be aligned with the .mp3 files.',
        dest='transcriptions_dir')

    parser.add_argument(
        '--gentle-dir', '-g', type=str,
        default='gentle_align',
        help='Relative path from data_dir to the directory where all of the'
        ' results from aligning the files will be stored as .json files.',
        dest='gentle_dir')

    parser.add_argument(
        '--overwrite', '-o', action='store_true',
        help='Overwrites the alignment file if it already exists.',
        dest='overwrite')

    parser.add_argument(
        '--no-overwrite', '-n', action='store_false',
        help='Does not overwrite already existing alignment files (the default'
        ' behavior).', dest='overwrite')

    parser.add_argument(
        '--praat-textgrid', '-p', action='store_true',
        help='Writes a Praat .TextGrid file to the same directory that '
        'contains the .mp3 files with the timing information that was '
        'extracted from the gentle aligner (the default behavior).',
        dest='praat_textgrid')

    parser.add_argument(
        '--no-praat-textgrid', '-x', action='store_false',
        help='Doesn\'t write a Praat .TextGrid file.',
        dest='praat_textgrid')

    parser.set_defaults(praat_textgrid=True, overwrite=False)

    parser.add_argument(
        '--log', '-l', type=str,
        default='warning',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Set the logging level.',
        dest='log')

    args = parser.parse_args()

    aligner = Aligner(args.file_, args.data_dir, args.mp3_dir,
                      args.transcriptions_dir, args.gentle_dir)

    set_class_log_level(aligner, args.log)

    aligner.align(args.overwrite, args.praat_textgrid)
    aligner.get_timing_info()
