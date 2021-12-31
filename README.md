# Wiktionary2Migaku

Turn wiktionary database dumps into dictionaries that [Migaku](https://www.migaku.io/tools-guides) accepts.

The parser uses regex and generators to quickly sift through the large database dumps.

## Note

Before continuing, check the [languages](./src/languages) folder to see if your language is supported. This project was created for parsing the French Wiktionary and currently only supports that language. The editing standards may also be different and require different regex.

## Installation

1. Get the database dump from [Wikimedia Downloads](https://dumps.wikimedia.org/backup-index.html)
    - Look for the filename that ends with `-pages-articles.xml.bz2`.
2. Extract the `.bz2` file somewhere
    - This should result in a nested folder with a large XML file
    - This project will work with any text file that contains wikicode
3. Setup the project:

```bash
$ python3 -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

## Usage

1. Get your target language code from [Wiktionary's List of Languages](https://en.wiktionary.org/wiki/Wiktionary:List_of_languages)
2. Run the program (`python run.py`) with the arguments listed below:

```
usage: run.py [-h] [-s] -l LANGUAGE_CODE -i INPUT_FILE

Parse wiktionary dump into Migaku Dictionary Format

optional arguments:
  -h, --help            show this help message and exit
  -s, --no-progress-bar
                        Don't use progress bar. Faster since it skips the
                        initial count of total terms, but does not give an
                        ETA.
  -l LANGUAGE_CODE, --language-code LANGUAGE_CODE
                        Wiktionary Language Code
  -i INPUT_FILE, --input-file INPUT_FILE
                        Absolute file path of input text file to parse
```

## Tests

```
python -m unittest [discover]
```