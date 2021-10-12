import os
import logging
import logging.config
import pandas as pd


logger = logging.getLogger(__name__)


class TranscriptionExtractor:
    def __init__(
            self,
            transcribed_csv,
            transcription_col_name,
            data_dir,
            overwrite):
        self.logger = logger.getChild(self.__class__.__name__)
        self.transcribed_csv = transcribed_csv
        self.transcription_col_name = transcription_col_name
        self.data_dir = data_dir
        self.overwrite = overwrite

    def get_transcriptions(self):
        df = pd.read_csv(self.transcribed_csv)
        groupings = df.groupby('Participant')
        for _, grp_df in groupings:
            self.extract_transcriptions(
                grp_df,
                self.transcription_col_name,
                self.data_dir)

    def extract_transcriptions(self, grp_df, col_name, data_dir):
        p = str(grp_df['Participant'].unique()[0])
        transcriptions = grp_df[col_name].tolist()

        transcriptions_dir = os.path.join(
            data_dir, 'transcriptions', p)
        if not os.path.exists(transcriptions_dir):
            os.makedirs(transcriptions_dir)
            self.logger.info(
                'Created directory:\n%(dir)s' % {'dir': transcriptions_dir})

        for i, t in enumerate(transcriptions):
            if str(t) == 'nan':
                self.logger.warning(
                    'Missing transcription for item %(i)s for participant '
                    '%(p)s' % {'i': i + 1, 'p': p})
            else:
                f = os.path.join(
                    transcriptions_dir, str(i + 1).zfill(2) + '.txt')

                if os.path.exists(f) and not self.overwrite:
                    self.logger.info('File, %(f)s, already exists. Skipping.' %
                                     {'f': f})

                if os.path.exists(f) and self.overwrite:
                    self.logger.info('File, %(f)s, already exists. '
                                     'Overwriting.' % {'f': f})

                if self.overwrite or not os.path.exists(f):
                    with open(f, 'w', encoding='utf-8') as file_:
                        file_.write(str(t) + '\n')
                    self.logger.info('Wrote file %(f)s' % {'f': f})


def main():
    import argparse
    from . import log_conf
    from .utils import set_class_log_level

    logging.config.dictConfig(log_conf)

    parser = argparse.ArgumentParser(
        description='Extracts transcriptions from a .csv file to a single '
        'file per transcription for input into a forced aligner.')

    parser.add_argument(
        '--file', '-f', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/'
        'data/exp1_data/ibex_results/exp1_data_tidy_transcribed.csv',
        help='',
        dest='file_')

    parser.add_argument(
        '--tcol', '-t', type=str,
        default='Transcription',
        help='Name of the column in the .csv file containing the '
        'transcriptions.',
        dest='tcol')

    parser.add_argument(
        '--data-dir', '-d', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/'
        'data/exp1_data',
        help='Directory in which to put the transcriptions directory, which is'
        ' where an individual .txt file will be saved for each transcription.',
        dest='data_dir')

    parser.add_argument(
        '--no-overwrite', '-n', action='store_false',
        help='Only extracts transcriptions for participants who don\'t yet '
        'have individual transcription files (the default behavior).',
        dest='overwrite')

    parser.add_argument(
        '--overwrite', '-o', action='store_true',
        help='Re-extracts transcriptions for all participants in case the '
        'transcription in the .csv file has changed.',
        dest='overwrite')

    parser.set_defaults(overwrite=False)

    parser.add_argument(
        '--log', '-l', type=str,
        default='warning',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Set the logging level.',
        dest='log')

    args = parser.parse_args()

    extractor = TranscriptionExtractor(
        args.file_, args.tcol, args.data_dir, args.overwrite)

    set_class_log_level(extractor, args.log)

    extractor.get_transcriptions()
