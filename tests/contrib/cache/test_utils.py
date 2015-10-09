# -*- coding: utf-8 -*-
from librarian_core.contrib.cache import utils as mod


def test_generate_key(base_cache):
    known_md5 = 'f3e993b570e3ec53b3b05df933267e6f'
    generated_md5 = mod.generate_key(1, 2, 'ab', name='something')
    assert generated_md5 == known_md5


def test_generate_key_with_weird_data(base_cache):
    known_md5 = '4dc1a960cb2d99175da541ff089e5045'
    generated_md5 = mod.generate_key(None,
                                     u'les misérable',
                                     u'åß∂ƒ©˙∆˚¬…æ',
                                     u'社會科學院語學研究所')
    assert generated_md5 == known_md5
