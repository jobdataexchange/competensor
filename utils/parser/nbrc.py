import pandas as pd
from io import StringIO
from pathlib import Path

regex_for_roman_numeral = r'(?P<roman>I+?)\.'
regex_for_uppercase_letters = r'(?P<uppper>^[A-H|J-Z])\.'
regex_for_lowercase_letters = r'(?P<lower>^[a-z])\.'    
regex_for_bullets = r'(?P<bullets>\* )'
regex_for_numbers = r'(?P<number>^\d)\.'
regex_for_text = r'[\.|:]\s(?P<text>.*)'


def get_series(file_path='./frameworks/Therapist-Multiple-Choice-DCO-NBRC.txt'):
    df = pd.read_csv(
        StringIO(
            Path(file_path).read_text()
        ), sep='\n', header=None)
    df = \
        df.apply(
            lambda x: x.str.strip()
        )        
    df['roman'] = df.iloc[:, 0].str.extract(regex_for_roman_numeral)
    df['uppercase'] = df.iloc[:, 0].str.extract(regex_for_uppercase_letters)
    df['lowercase'] = df.iloc[:, 0].str.extract(regex_for_lowercase_letters)    
    df['numbers'] = df.iloc[:, 0].str.extract(regex_for_numbers)
    df['bullets'] = df.iloc[:, 0].str.extract(regex_for_bullets)    
    df['text'] = df.iloc[:, 0].str.extract(regex_for_text)

    null_text = df['text'].isnull()
    df.loc[null_text, 'text'] = df[null_text].iloc[:, 0]
    df['text'].dropna(inplace=True)
    df['text'] = df['text'].str.replace('\d+', '')\
                           .str.replace('.', '')\
                           .str.replace('*', '')

    is_roman = df.roman.notnull()

    df['roman'].ffill(inplace=True)
    df['uppercase'].ffill(inplace=True)
    df.loc[is_roman, 'uppercase'] = pd.np.nan
    df['numbers'].ffill(inplace=True)

    null_text = df['text'].isnull()
    df.loc[null_text, 'text'] = df[null_text].iloc[:, 0]
    df['text'].dropna(inplace=True)

    return df
