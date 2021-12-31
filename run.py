import os
import sys
import json
import argparse
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, os.path.abspath('./src'))

from parser import Parser


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return json.JSONEncoder.default(self, obj)


def main(language_code: str, input_file_path: str, progress_bar: bool = True):
    p = Parser(language_code, input_file_path)
    if progress_bar:
        print('Counting terms. This will take a few minutes...')
        total_terms = p.count_terms()
        print('Done counting. Total terms:', total_terms)
    else:
        total_terms = None
    first_item = True
    with open('wiktionary.json', 'w', encoding='utf-8') as o:
        o.write('[')
        for term in tqdm(p.parse(), total=total_terms):
            if first_item:
                o.write(json.dumps(term, ensure_ascii=False, cls=JSONEncoder))
                first_item = False
            else:
                o.write("," + json.dumps(term, ensure_ascii=False, cls=JSONEncoder))
        o.write(']')


if __name__ == '__main__':
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description="Parse wiktionary dump into Migaku Dictionary Format")
    parser.add_argument('-s', '--no-progress-bar', dest='progress_bar', action='store_false', help="Don't use progress bar. Faster since it skips the initial count of total terms, but does not give an ETA.")
    parser.add_argument('-l', '--language-code', type=str, help="Wiktionary Language Code", required=True)
    parser.add_argument('-i', '--input-file', type=str, help="Absolute file path of input text file to parse", required=True)
    args = parser.parse_args()
    main(args.language_code, args.input_file, args.progress_bar)
