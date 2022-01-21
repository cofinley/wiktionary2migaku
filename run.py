import os
import sys
import json
import argparse
from typing import Type
from multiprocessing import Pool

from tqdm import tqdm

sys.path.insert(0, os.path.abspath('./src'))

from language_parsers import LANGUAGE_PAIR_PARSERS
from language_parsers._language_pair_parser import LanguagePairParser

CHUNKSIZE = 1000


def main(
        input_file_path: str,
        dump_language_code: str,
        definition_language_code: str
) -> None:
    """
    Parse Wiktionary dump, write results to json file
    :param input_file_path: file path to Wiktionary dump
    :param dump_language_code: Language code of the Wiktionary dump
    :param definition_language_code: Language code of the definitions to get
    """
    # Open in binary mode to allow seeking at the end to remove trailing comma
    # This is done instead of putting in `if first_item then don't put comma` in the tight loop
    json_out = open('wiktionary_imap.json', 'wb')
    json_out.write(b'[')

    parser = get_parser(input_file_path, dump_language_code, definition_language_code)
    print('Counting pages...')
    page_count = parser.count_pages()
    print('Total pages:', page_count)
    with Pool() as p:
        page_iter = tqdm(p.imap_unordered(parser.parse_page, parser.parse_dump(), chunksize=CHUNKSIZE), unit='page', total=page_count)
        for page_terms in page_iter:
            for term in page_terms:
                line = json.dumps(term, ensure_ascii=False) + ','
                json_out.write(bytes(line, encoding='utf-8'))
    # Remove trailing comma
    json_out.seek(-1, os.SEEK_END)
    json_out.truncate()
    json_out.write(b']')


def get_parser(
        input_file_path: str,
        dump_language_code: str,
        definition_language_code: str
) -> Type[LanguagePairParser]:
    lookup_key = f'{dump_language_code}_{definition_language_code}'
    try:
        parser_class = LANGUAGE_PAIR_PARSERS[lookup_key]
    except KeyError:
        msg = f'Language pair not found for dump language {dump_language_code} and definition language {definition_language_code}'
        exit(msg)
    parser = parser_class(input_file_path)
    return parser


if __name__ == '__main__':
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description='Parse wiktionary dump into Migaku Dictionary Format')
    parser.add_argument('-l1', '--dump-language-code', type=str, help='Language code of the dump file (e.g. en, es, fr)', required=True)
    parser.add_argument('-l2', '--definition-language-code', type=str, help='Language code of the definitions to get within the dump (e.g. en, es, fr)', required=True)
    parser.add_argument('-i', '--input-file', type=str, help='Absolute file path of input text file to parse', required=True)
    args = parser.parse_args()
    main(args.input_file, args.dump_language_code, args.definition_language_code)
