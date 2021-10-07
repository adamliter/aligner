from setuptools import setup, find_packages


setup(
    name='aligner',
    version='0.0.1',
    description='Various Python utilities for converting speech to text, force'
    ' aligning the transcription with the audio, and extracting timing '
    'information for a linguistics production experiment.',
    author='Adam Liter',
    author_email='io@adamliter.org',
    packages=find_packages(where='src'),
    package_dir={
        '': 'src', },
    entry_points={
        'console_scripts': [
            'to_mp3 = aligner.mp3:main',
            'transcribe = aligner.stt:main']},
    install_requires=[
        'PyYaml',
        'pandas',
        'pydub',
        'google-cloud-speech',
    ])
