import os
import io
import logging.config
import pandas as pd
from google.cloud import speech
from pydub import AudioSegment
from pydub.utils import mediainfo


logger = logging.getLogger(__name__)


class SpeechToText:
    def __init__(self, mp3_dir, data_dir, transcribed_csv,
                 transcription_col_name, save_every_n):
        self.logger = logger.getChild(self.__class__.__name__)
        self.data_dir = data_dir
        self.mp3_dir = os.path.join(data_dir, mp3_dir)
        self.transcribed_csv = transcribed_csv
        self.transcription_col_name = transcription_col_name
        self.save_every_n = save_every_n
        self.client = speech.SpeechClient()

    def transcribe(self):
        df = pd.read_csv(self.transcribed_csv)

        # If there aren't yet any strings in the Transcription column, pandas
        # will treat it as a float, so we must cast it to a string
        df = df.astype({self.transcription_col_name: str}, errors='raise')
        df[self.transcription_col_name] = \
            df[self.transcription_col_name].replace('nan', pd.NA)

        i = 1
        for idx in df[df[self.transcription_col_name].isna()].index:
            p = df.iloc[idx]['Participant']
            item = df.iloc[idx]['ItemNumber']

            mp3_file = os.path.join(
                self.mp3_dir, f'{p}/item_number_{item:02}.mp3')
            try:
                mp3 = AudioSegment.from_mp3(mp3_file)
                info = mediainfo(mp3_file)
                self.logger.debug(
                    'Audio file, %(mp3_file)s has %(channel)s channel(s).' %
                    {'mp3_file': mp3_file, 'channel': info['channels']})
                content = io.BytesIO()
                # Convert to flac since the Google Cloud speech-to-text support
                # for .mp3 files is only in beta mode so far
                mp3.export(content, format='flac')

                audio = speech.RecognitionAudio(content=content.read())
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
                    language_code='en-US',
                    audio_channel_count=int(info['channels']))
                self.logger.info(
                    'Submitting .mp3 file for item number %(item)s for '
                    'participant %(p)s to Google\'s Speech-to-Text service.' %
                    {'p': p, 'item': item})
                response = self.client.recognize(config=config, audio=audio)
                self.logger.debug(
                    'Response from Google\'s Speech-to-Text service:\n'
                    '%(response)s' % {'response': response})
                transcription = \
                    response.results[0].alternatives[0].transcript\
                                                       .capitalize() + '?'

                df.at[idx, self.transcription_col_name] = transcription

                if i % self.save_every_n == 0:
                    df.to_csv(self.transcribed_csv, na_rep='NA', index=False)
                    self.logger.debug(
                        'Saved file %(f)s' %
                        {'f': self.transcribed_csv})
                i += 1

            except FileNotFoundError:
                self.logger.warning(
                    'File not found: %(mp3_file)s. Skipping.' %
                    {'mp3_file': mp3_file})

        df.to_csv(self.transcribed_csv, na_rep='NA', index=False)
        self.logger.debug(
            'Saved file %(f)s' %
            {'f': self.transcribed_csv})


def main():
    import argparse
    from . import log_conf
    from .utils import set_class_log_level

    logging.config.dictConfig(log_conf)

    parser = argparse.ArgumentParser(
        description='Attempts a first-pass transcription of the .mp3 files '
        'using Google Cloud\'s Speech-to-Text APIs.')

    parser.add_argument(
        '--file', '-f', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/'
        'data/exp1_data/ibex_results/exp1_data_tidy_transcribed.csv',
        help='Name of the .csv file to read/write with the transcriptions.',
        dest='file_')

    parser.add_argument(
        '--tcol', '-t', type=str, default='Transcription',
        help='Name of the column in the .csv file containing the '
        'transcriptions.', dest='tcol')

    parser.add_argument(
        '--data-dir', '-d', type=str,
        default='/Users/adamliter/Dropbox/Research/PlanningWindow/'
        'data/exp1_data/',
        help='Parent directory which contains all the transcription directory,'
        'ibex_results directory, mp3 directory, etc..', dest='data_dir')

    parser.add_argument(
        '--mp3-dir', '-m', type=str, default='mp3_files',
        help='Relative path from the data directory to the directory with '
        'the .mp3 files.', dest='mp3_dir')

    parser.add_argument(
        '--save-every-n', '-n', type=int, default=10,
        help='Save results to disk after every n submissions to Google\'s '
        'Speech-to-Text API (default is 10). This avoids being billed for '
        '(too many) resubmissions in case the script errors out and you have '
        'to rerun it after fixing the error. Setting to 1 increases disk I/O '
        'but maximizes money savings.',
        dest='save_every_n')

    parser.add_argument(
        '--credentials', '-c', type=str,
        help='Path to .json credentials file for Google Cloud authentication.',
        default='')

    parser.add_argument(
        '--log', '-l', type=str,
        default='warning',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Set the logging level.',
        dest='log')

    args = parser.parse_args()

    if args.credentials != '':
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = args.credentials

    transcriber = SpeechToText(
        args.mp3_dir, args.data_dir, args.file_, args.tcol, args.save_every_n)

    set_class_log_level(transcriber, args.log)

    transcriber.transcribe()
