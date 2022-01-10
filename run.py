import os
import sys
import json
import math
import argparse
from typing import List
from pathlib import Path
from functools import partial
from multiprocessing import Pool, cpu_count, RLock

from tqdm import tqdm

sys.path.insert(0, os.path.abspath('./src'))

from parser import Parser


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return json.JSONEncoder.default(self, obj)


def main(
        input_file_path: str,
        language_code: str,
        progress_bar: bool = True,
        multi_process: bool = True,
        reuse_partition_files: bool = False
):
    if multi_process:
        func = run_multi_process(input_file_path, language_code, progress_bar=progress_bar, reuse_partition_files=reuse_partition_files)
    else:
        func = run_single_process(input_file_path, language_code, progress_bar=progress_bar)


def run_single_process(
        input_file_path: str,
        language_code: str,
        progress_bar: bool = True
) -> None:
    """
    Parse entire Wiktionary dump with single process
    :param input_file_path: file path to Wiktionary dump
    :param language_code: Wiktionary language code to search for
    :param progress_bar: Show progress?
    """
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


def run_multi_process(
        input_file_path: str,
        language_code: str,
        progress_bar: bool = True,
        reuse_partition_files: bool = False
) -> None:
    """
    Parse entire Wiktionary dump with as many CPU cores as you have.
    Partitions the dump, processes each partition into JSON, then combines the
    result into one file JSON file.
    :param input_file_path: file path to Wiktionary dump
    :param language_code: Wiktionary language code to search for
    :param progress_bar: Show progress?
    :param reuse_partition_files: Reuse partitioned dump files for quicker testing?
    """
    num_cpus = cpu_count()
    partition_filenames = partition_file(input_file_path, num_partitions=num_cpus, reuse_partition_files=reuse_partition_files)
    pool = Pool(processes=num_cpus, initargs=(RLock(),), initializer=tqdm.set_lock)
    jobs = [
        pool.apply_async(process_file, args=(i, filename, language_code, progress_bar))
        for i, filename in enumerate(partition_filenames)
    ]
    pool.close()
    output_file_paths = [job.get() for job in jobs]
    print("\n" * (len(partition_filenames) + 1))
    combine_files(output_file_paths)
    if not reuse_partition_files:
        remove_partition_files(partition_filenames)


def partition_file(
        filepath: str,
        num_partitions: int,
        reuse_partition_files: bool = False
) -> List[str]:
    """
    Split file into ``num_partitions``
    Partition will use a blank line as a separator and won't partition
    in the middle of a text block.
    """
    filenames = [f'{i+1}.tmp' for i in range(num_partitions)]
    if reuse_partition_files:
        if all(os.path.exists(filename) for filename in filenames):
            print('Using existing partition files from previous run:', filenames)
            return filenames
        else:
            print("Partition files don't exist yet, but will be preserved after this run.")

    line_count = get_line_count(filepath)
    partition_size = math.ceil(line_count / num_partitions)
    print('Number of lines:', line_count, '; Number of partitions:', num_partitions, '; Lines per partition:', partition_size)
    count = 0

    file_handlers = [open(filename, 'a', encoding='utf-8') for filename in filenames]

    with open(filepath, encoding='utf-8') as f:
        partition_num = 0
        file_handler = file_handlers[partition_num]
        print(f'Writing to partition file {partition_num+1}/{num_partitions}:', file_handler.name)
        for line in f:
            file_handler.write(line)
            count += 1
            if count >= partition_size and not line.strip():
                count = 0
                partition_num += 1
                file_handler = file_handlers[partition_num]
                print(f'Writing to partition file {partition_num+1}/{num_partitions}:', file_handler.name)

    for fh in file_handlers:
        fh.close()
    return filenames


def get_line_count(filename: str) -> int:
    """
    Get line count (\n) using buffer + generator
    """
    # https://stackoverflow.com/a/68385697/3203662
    def _make_gen(reader):
        while True:
            b = reader(2 ** 16)
            if not b: break
            yield b

    with open(filename, 'rb') as f:
        count = sum(buf.count(b"\n") for buf in _make_gen(f.raw.read))
    return count


def process_file(
        pid: int,
        input_file_path: str,
        language_code: str,
        progress_bar: bool = True
) -> str:
    """
    Process individual partition file
    """
    p = Parser(language_code, input_file_path)
    if progress_bar:
        print(f'Counting terms for partition {pid}. This will take a few minutes...')
        total_terms = p.count_terms()
        print('Done counting. Total terms:', total_terms)
    else:
        total_terms = None
    first_item = True
    output_file_path = input_file_path + '.json'
    with open(output_file_path, 'w', encoding='utf-8') as o:
        for term in tqdm(p.parse(), total=total_terms, position=pid+1, unit='term'):
            if first_item:
                o.write(json.dumps(term, ensure_ascii=False, cls=JSONEncoder))
                first_item = False
            else:
                o.write("," + json.dumps(term, ensure_ascii=False, cls=JSONEncoder))
    return output_file_path


def combine_files(output_file_paths: List[str]) -> None:
    """
    Combine parsed (JSON) partition files into one
    """
    print('Combining processed partitions...')
    with open('wiktionary.json', 'w', encoding='utf-8') as o:
        o.write('[')
        first_file = True
        for temp_file in output_file_paths:
            if first_file:
                first_file = False
            else:
                o.write(',')
            with open(temp_file, encoding='utf-8') as f:
                for line in f:
                    o.write(line)
        o.write(']')
    print('Combined processed partitions.')


def remove_partition_files(partition_filenames: List[str]) -> None:
    print('Removing partition files...')
    for filename in partition_filenames:
        json_partition_filename = filename + '.json'
        os.remove(filename)
        os.remove(json_partition_filename)
    print('Removed partition files.')


if __name__ == '__main__':
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(description='Parse wiktionary dump into Migaku Dictionary Format')
    parser.add_argument('-s', '--no-progress-bar', dest='progress_bar', action='store_false', help="Don't use progress bar. Faster since it skips the initial count of total terms, but does not give an ETA.")
    parser.add_argument('-p', '--single-process', dest='multi_process', action='store_false', help='Run as single process (slower)')
    parser.add_argument('-r', '--reuse-partition-files', action='store_true', help='Reuse partitioned dump files for quicker testing. Does not apply if using -p/--single-process.')
    parser.add_argument('-l', '--language-code', type=str, help='Wiktionary Language Code', required=True)
    parser.add_argument('-i', '--input-file', type=str, help='Absolute file path of input text file to parse', required=True)
    args = parser.parse_args()
    main(args.input_file, args.language_code, args.progress_bar, args.multi_process, args.reuse_partition_files)
