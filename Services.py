import streamlit as st
import re
import pandas as pd
import numpy as np
import emoji
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from stop_words import get_stop_words
import datetime
from langdetect import detect


class Services:
    # @st.cache

    def detect_chat_language(chat_file, chat_language):
        lines = str(chat_file.getvalue())
        chat_language = detect(chat_file.getvalue())
        return chat_language

    def is_group_chat(members):
        if members.shape[0] > 3:
            return True
        else:
            return False

    def detect_export_language(chat_file, export_language):
        lines = str(chat_file.getvalue())
        patterns = [
            '‎[\s\S]*(image omitted)[\s\S]',
            '[\s\S]*(video omitted)[\s\S]',
            '[\s\S]*(GIF omitted)[\s\S]',
            '[\s\S]*(audio omitted)[\s\S]',
        ]
        pattern = '^' + '|'.join(patterns)
        result = re.match(pattern, lines)
        if result:
            export_language = "ENG"
        else:
            patterns = [
                '‎[\s\S]*(Scheda contatto omessa)[\s\S]',
                '[\s\S]*(immagine omessa)[\s\S]',
                '[\s\S]*( omesso)[\s\S]',
                '[\s\S]*(GIF esclusa)[\s\S]',
                '[\s\S]*(sticker non incluso)[\s\S]',
            ]
            pattern = '^' + '|'.join(patterns)
            result = re.match(pattern, lines)
            if result:
                export_language = "ITA"
        return export_language



    def FindAuthor(s):
        patterns = [
            '([\w]+):',  # First Name
            '([\w]+[\s]+[\w]+):',  # First Name + Last Name
            '([\s\S]+[+]*[\d]{2}[\s]+[\d]{3}[\s]+[\d]{3}[\s]+[\d]{4}[\D]+):',  # Mobile Number (IT)
            '([\w]+)[\u263a-\U0001f999]+:',
        ]
        pattern = '^' + '|'.join(patterns)
        result = re.match(pattern, s)
        if result:
            return True
        return False

    # @st.cache
    def startsWithDateAndTimeAndroid(s):
        pattern = '^([0-9]+)(\/)([0-9]+)(\/)([0-9]+), ([0-9]+):([0-9]+)[ ]?(AM|PM|am|pm)? -'
        result = re.match(pattern, s)
        if result:
            return True
        return False

    # @st.cache
    def startsWithDateAndTimeios(s):
        pattern = '^([\s\S]*)\[([0-9]+)([\/-])([0-9]+)([\/-])([0-9]+)[,]? ([0-9]+):([0-9][0-9]):([0-9][0-9])?[ ]?(AM|PM|am|pm)?\]'
        result = re.match(pattern, s)
        if result:
            return True
        return False

    # @st.cache
    def getDataPointAndroid(line):
        splitLine = line.split(' - ')
        dateTime = splitLine[0]
        date, time = dateTime.split(', ')
        message = ' '.join(splitLine[1:])
        if Services.FindAuthor(message):
            splitMessage = message.split(':')
            author = splitMessage[0]
            message = ' '.join(splitMessage[1:])
        else:
            author = None
        return date, time, author, message

    # @st.cache
    def getDataPointios(line):
        splitLine = line.split('] ')
        dateTime = splitLine[0]
        if ',' in dateTime:
            date, time = dateTime.split(',')
        else:
            date, time = dateTime.split(' ')
        message = ' '.join(splitLine[1:])
        if Services.FindAuthor(message):
            splitMessage = message.split(':')
            author = splitMessage[0]
            message = ''.join(splitMessage[1:])
        else:
            author = None
        if time[5] == ":":
            time = time[:5] + time[-3:]
        else:
            if 'AM' in time or 'PM' in time:
                time = time[:6] + time[-3:]
            else:
                time = time[:6]
        return date, time, author, message

    # @st.cache
    def split_count(text):

        emoji_list = []
        data = re.findall(r"["
                          u"\U0001F600-\U0001F64F"  # emoticons
                          u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                          u"\U0001F680-\U0001F6FF"  # transport & map symbols
                          u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                          "]+", text)
        for word in data:
            if any(char in emoji.UNICODE_EMOJI for char in word):
                emoji_list.append(word)

        return emoji_list

    # @st.cache
    def dateconv(date):
        year = ''
        if '-' in date:
            year = date.split('-')[2]
            if len(year) == 4:
                return datetime.datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")
            elif len(year) == 2:
                return datetime.datetime.strptime(date, "%d-%m-%y").strftime("%Y-%m-%d")
        elif '/' in date:
            year = date.split('/')[2]
            if len(year) == 4:
                return datetime.datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
            if len(year) == 2:
                return datetime.datetime.strptime(date, "%d/%m/%y").strftime("%Y-%m-%d")