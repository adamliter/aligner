import os
import logging
import logging.config
import pandas as pd
from zipfile import ZipFile
from pydub import AudioSegment


logger = logging.getLogger(__name__)


class WebmToMp3Converter:
    def __init__(self, tidy_csv, mp3_dir, zip_dir, overwrite):
        self.logger = logger.getChild(self.__class__.__name__)
        self.tidy_csv = tidy_csv
        self.mp3_dir = mp3_dir
        self.zip_dir = zip_dir
        self.overwrite = overwrite

    def convert_to_mp3(self):
        df = pd.read_csv(self.tidy_csv)
        groupings = df.groupby('Participant')
        for p, grp_df in groupings:
            self.logger.info('Working on data for participant %(p)s.' %
                             {'p': p})
            self.convert_and_cut(grp_df, self.mp3_dir, self.zip_dir)

    def convert_and_cut(self, grp_df, mp3_dir, zip_dir):
        mp3_dir = os.path.join(
            mp3_dir, str(grp_df['Participant'].unique()[0]))
        if not os.path.exists(mp3_dir):
            self.logger.info(
                'Creating individual directory for participant\'s .mp3 files:'
                '\n%(mp3_dir)s' %
                {'mp3_dir': mp3_dir})
            os.makedirs(mp3_dir)

        zf = os.path.join(zip_dir, grp_df['RecordingsArchive'].unique()[0])

        try:
            with ZipFile(zf) as z:
                self.logger.info(
                    'Opened zip file:\n%(zf)s' %
                    {'zf': zf})
                for i, file_ in enumerate(grp_df['WebmFileName']):

                    mp3_name = os.path.join(
                        mp3_dir,
                        'item_number_' + str(i + 1).zfill(2) + '.mp3')

                    if os.path.exists(mp3_name) and not self.overwrite:
                        self.logger.info(
                            'The .mp3 file, %(mp3_name)s, already exists. '
                            'Skipping.' % {'mp3_name': mp3_name})

                    elif os.path.exists(mp3_name) and self.overwrite:
                        self.logger.info(
                            'The .mp3 file, %(mp3_name)s, already exists. '
                            'Overwriting.' % {'mp3_name': mp3_name})

                    if not os.path.exists(mp3_name) or self.overwrite:
                        start_time = float(
                            grp_df[grp_df['WebmFileName'] == file_]
                            ['SecondsToStripFromFrontOfRecording'] *
                            1000) + 500
                        with z.open(file_) as webm:
                            sound = AudioSegment.from_file(webm)
                            extracted_sound = sound[start_time:]
                            extracted_sound.export(mp3_name, format='mp3')
                            self.logger.info('Saved .mp3 file:\n%(mp3_name)s' %
                                             {'mp3_name': mp3_name})
        except FileNotFoundError:
            self.logger.warning(
                'Archive file %(zf)s for participant not found. Skipping' %
                {'zf': zf})


def main():
    import argparse
    from . import log_conf
    from .utils import set_class_log_level

    logging.config.dictConfig(log_conf)

    parser = argparse.ArgumentParser(
        description='Converts .webm files to .mp3 files from a PCIbex '
        'experiment, based on a tidied .csv file that has been extracted '
        'from the PCIbex results file.')

    parser.add_argument(
        '--file', '-f', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/'
        'data/exp1_data/ibex_results/exp1_data_tidy.csv',
        help='Path to the tidied .csv file.',
        dest='file_')

    parser.add_argument(
        '--log', '-l', type=str,
        default='warning',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Set the logging level.',
        dest='log')

    parser.add_argument(
        '--mp3-dir', '-m', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/'
        'data/exp1_data/mp3_files/',
        help='Path to the directory where directories for each participant '
        'should be created in which to save the .mp3 files.',
        dest='mp3_dir')

    parser.add_argument(
        '--zip-dir', '-z', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/'
        'data/exp1_data/zip_archives/',
        help='Path to the directory containing all of the zip archives '
        'with the recordings.',
        dest='zip_dir')

    parser.add_argument(
        '--overwrite', '-o', action='store_true',
        help='Recreates .mp3 files for all participants (the default). This is'
        ' the default in case the amount of time to strip from the front of '
        'the recording is changed.',
        dest='overwrite')

    parser.add_argument(
        '--no-overwrite', '-n', action='store_false',
        help='Only extracts .mp3 files for participants who don\'t yet have '
        'any .mp3 files.',
        dest='overwrite')

    parser.set_defaults(overwrite=True)

    args = parser.parse_args()

    converter = WebmToMp3Converter(
        args.file_, args.mp3_dir, args.zip_dir, args.overwrite)

    set_class_log_level(converter, args.log)

    converter.convert_to_mp3()
