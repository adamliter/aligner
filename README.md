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
- `transcribe`
- `extract`

### `to_mp3`

To see help information, you can run `to_mp3 --help` after installing
the package (and assuming the virtual environment into which you
installed the package is active).

Example usage:

``` sh
to_mp3 -l info -f data/ibex_results/example_data_tidy.csv -m data/mp3_files -z data/zip_archives
```

### `transcribe`

To see help information, you can run `trascribe --help` after installing
the package (and assuming the virtual environment into which you
installed the package is active).

To use this utility, you will need a Google Cloud account. You can sign
up for a free trial. After creating a Google Cloud account, navigate to
[`https://console.cloud.google.com/speech`][speech-to-text]. If you
haven't already created a project, you will need to do so.

After creating the project, click the "Enable API" button:

![Picture showing "Enable API" button](imgs/speech-to-text-enable-api.png)

Next, navigate to
[`https://console.cloud.google.com/iam-admin/serviceaccounts`][serviceaccounts],
and select your newly created project. For this project, click "Create
Service Account" to add a service account. Name it whatever you'd like,
and then click "Create and Continue":

![Picture showing creation of Service Account](imgs/google-cloud-create-service-account.png)

Finally, give the Service Account a role so that it can use the
Speech-to-Text service. I gave my service account the Editor role from
the Basic list:

![Picture showing how to assign the editor role](imgs/google-cloud-assign-editor-role.png)

Then hit the 'Done' button. Next, click on the newly created Service
Account, and navigate to the 'KEYS' tab:

![Picture showing the keys tab](imgs/google-cloud-service-account-keys.png)

Click the 'ADD KEY' dropdown and then click 'Create new key'. Add a
.json key, which will be downloaded to your computer.

Now, you can use this utility like so:

``` sh
transcribe -l info -f data/ibex_results/example_data_tidy_transcribed.csv -t Transcription -d data/ -m mp3_files -c /path/to/json/credentials/file.json -n 8
```


### `extract`

To see help information, you can run `extract --help` after installing
the package (and assuming the virtual environment into which you
installed the package is active).

Example usage:

``` sh
extract -l info -d data -f data/ibex_results/example_data_tidy_transcribed.csv -t Transcription -n
```


<!-- Links -->
[speech-to-text]: https://console.cloud.google.com/speech
[serviceaccounts]: https://console.cloud.google.com/iam-admin/serviceaccounts
