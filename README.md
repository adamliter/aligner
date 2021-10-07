<!-- -*- mode: gfm; fill-column: 72; coding: utf-8; -*- -->
# aligner

This is a Python package that provides varuous utilities for converting
speceh to text, force aligning the transcription with the audio, and
extracting timing information for a linguistics production experiment
that I'm conducting.

## Example usage

After cloning the repository, you can install the package locally in a
Python virtual environment, like so:

``` sh
pip install -e .
```

The package provides the following utilities:

- `to_mp3`

### `to_mp3`

To see help information, you can run `to_mp3 --help` after installing
the package (and assuming the virtual environment into which you
installed the package is active).

Example usage:

``` sh
to_mp3 -l info -f data/ibex_results/example_data_tidy.csv -m data/mp3_files -z data/zip_archives
```
