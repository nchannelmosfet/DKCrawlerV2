import os
import re
import json
import logging
import pandas as pd
from pandas.errors import EmptyDataError, ParserError
import functools
from playwright.async_api import Page


def get_batches(seq, batch_size=1):
    for i in range(0, len(seq), batch_size):
        yield seq[i:i + batch_size]


def get_file_list(_dir, suffix=None):
    files = []
    for dirpath, dirnames, filenames in os.walk(_dir):
        for filename in filenames:
            files.append(os.path.join(dirpath, filename))

    if suffix:
        files = [f for f in files if f.endswith(suffix)]
    return files


def get_latest_session_index(root):
    dirs = os.listdir(root)
    dirs = [os.path.join(root, _dir) for _dir in dirs if re.search(r'session\d+$', _dir, re.IGNORECASE)]
    try:
        latest_dir = max(dirs, key=os.path.getctime)
        latest_index = int(latest_dir.split('\\')[-1].replace('session', ''))
        return latest_index
    except ValueError:
        return 0


def concat_data(in_files):
    dfs = []
    for file in in_files:
        try:
            try:
                df = pd.read_csv(file)
            except (ParserError, UnicodeDecodeError):
                df = pd.read_excel(file, engine='openpyxl')
            dfs.append(df)
        except EmptyDataError:
            print(f'"{file}" is empty')
    combined_df = pd.concat(dfs, join='inner', ignore_index=True)
    return combined_df


def set_up_logger(logger_name, log_file_path=None):
    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s]: %(message)s',
        "%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(logger_name)
    if len(logger.handlers) > 0:
        logger.handlers.clear()
    logger.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file_path is not None:
        with open(log_file_path, 'w+') as f:
            f.write('')
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def read_urls(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    urls = [line for line in lines if (not line.startswith('#')) and len(line) > 0]
    return urls


def jsonify(obj):
    pretty_json = json.dumps(
        obj, indent=4, separators=(',', ': ')
    )
    return '\n' + pretty_json


def remove_url_qs(url):
    return url.split('?')[0]


def parse_int(s):
    return int(re.sub(r'\D', '', s))


def retry_on_exception(attempts: int = 5, delay: float = 10.0):
    """
    Decorator for retrying function on Exception
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            page: Page = kwargs["page"]
            logger = kwargs["logger"]

            exception = None
            for cur_attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as ex:
                    logger.info(f"retried {cur_attempt + 1} times")
                    exception = ex
                    await page.goto(page.url, timeout=60000)
                    logger.info(f"reload page")
                await page.wait_for_timeout(delay * 1000)
            raise exception
        return wrapper
    return decorator
