from typing import Dict, Generator, Iterable
from random import shuffle
from copy import deepcopy
import string

DEFAULT_SKIP_SYMBOLS = string.punctuation + string.whitespace + string.digits


def substitution_cipher(text: str, char_mapping: Dict[str, str]) -> str:
    """ Substitution cipher - replaces character based on char_mapping
    may rise ValueError Exception when incorrect mapping was provided
    """
    return u''.join([char_mapping.get(c) or c for c in text])


def chr_frequency(text: str, skip_symbols: str = '') -> Dict[str, int]:
    """ returns character frequeny in text
    Params:
        text (str): input text
        skip_symbols (str): string of skip symbols that are not counted
    """
    freq = {}
    for c in text:
        if c not in skip_symbols:
            freq.get(c) or freq.update({c: 0})
            freq[c] += 1
    return sort_dict(freq, reverse=True)


def rot_n_generator(text: str, rot_count: int, decrypt=False) -> Generator[str, str, str]:
    """ ROT cipher - shifts char in unicode table
    spaces are skipped for any operation, so translated as literal
    may rise ValueError Exception
    """
    direction = -1 if decrypt else 1
    for c in text:
        if c in string.whitespace:
            # yield same value
            yield c
        else:
            shifted_chr = (ord(c) + (rot_count % 32) * direction) % 0x110000
            yield chr(shifted_chr)


def sort_dict(d: Dict[str, int], reverse: bool = False) -> Dict[str, int]:
    """ returns sorted dict by value """
    return dict(sorted(d.items(), key=lambda item: item[1], reverse=reverse))


def random_shuffle_str(text: str) -> str:
    """ returns randomly shuffled string """
    shuffled_text = [*text]
    shuffle(shuffled_text)
    return ''.join(shuffled_text)


def random_shuffle_map(iterable: Iterable[str]) -> Dict[str, str]:
    """ returns randomly shuffled mapping for substitution """
    new_iterable = deepcopy(iterable)
    shuffle(new_iterable)
    shuffled_keys = {i: new_iterable.pop() for i in iterable}
    return shuffled_keys


def get_substitution_map_from_freqs(cipher_freq: Dict[str, int], sample_freq: Dict[str, int]) -> Dict[str, str]:
    """ returns character mapping based on comparison between cipher_freq and sample_freq
    both frequency dict should be reverse sorted
    """
    return {k: v for k, v in zip(cipher_freq.keys(), sample_freq.keys())}


def cal_error_rate(original_text: str, target_text: str) -> float:
    """ compares two texts and returns error rate in percentage """
    chr_len_original = len(original_text)
    chr_len_target = len(target_text)
    diffs = abs(chr_len_original - chr_len_target)
    i = 0
    correct = 0
    while chr_len_target > i < chr_len_original:
        if original_text[i] == target_text[i]:
            correct += 1
        diffs += 1 if original_text[i] != target_text[i] else 0
        i += 1

    return round(diffs / chr_len_original * 100, 2)


def get_top_n_letter_words(text: str, top: int = 3, number_of_letters: int = 3) -> Dict[str, int]:
    """ returns list of top N length repeating words in text """
    top = top if top < 5 else 5
    number_of_letters = number_of_letters if number_of_letters < 5 else 5
    words = text.split()
    n_letter_words_set = set(filter(lambda w: len(w) == number_of_letters, words))
    word_counts = {word: words.count(word) for word in n_letter_words_set}
    word_counts = sort_dict(word_counts, reverse=True)
    return {k: v for k, v in list(word_counts.items())[:top]}


def dict_get_key_by_value(d, value):
    keys = list(d.keys())
    values = list(d.values())
    index = values.index(value)
    return keys[index]


def substitute_word_as(source, target, char_mapping):
    if len(source) == len(target) and source != target:
        seen = []
        for i in range(0, len(source)):
            if source[i] != target[i]:
                source_key = dict_get_key_by_value(char_mapping, source[i])
                target_key = dict_get_key_by_value(char_mapping, target[i])
                if source_key not in seen:
                    seen.append(source_key)
                    # replace
                    char_mapping.update({source_key: target[i]})
                    char_mapping.update({target_key: source[i]})

    return char_mapping


def get_mapping_from_texts(text1, text2):
    mapping = {}
    max_len = len(text1)
    i = 0
    while i < max_len:
        if text2[i] not in DEFAULT_SKIP_SYMBOLS:
            mapping.update({text1[i]: text2[i]})
        i += 1

    return mapping
