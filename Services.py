import streamlit as st
import re
import pandas as pd
import numpy as np
import emoji
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from stop_words import get_stop_words
import datetime

class Services:
    # @st.cache
    def FindAuthor(s):
        patterns = [
            '([\w]+):',  # First Name
            '([\w]+[\s]+[\w]+):',  # First Name + Last Name
            '([\w]+[\s]+[\w]+[\s]+[\w]+):',  # First Name + Middle Name + Last Name
            '([\s\S]+[+]*[\d]{2}[\s]+[\d]{3}[\s]+[\d]{3}[\s]+[\d]{4}[\D]+)',  # Mobile Number (IT)
            '([\w]+)[\u263a-\U0001f999]+:',  # Name and Emoji
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
        pattern = '^\[([0-9]+)([\/-])([0-9]+)([\/-])([0-9]+)[,]? ([0-9]+):([0-9][0-9]):([0-9][0-9])?[ ]?(AM|PM|am|pm)?\]'
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
            message = ' '.join(splitMessage[1:])
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
                return datetime.datetime.strptime(date, "[%d-%m-%Y").strftime("%Y-%m-%d")
            elif len(year) == 2:
                return datetime.datetime.strptime(date, "[%d-%m-%y").strftime("%Y-%m-%d")
        elif '/' in date:
            year = date.split('/')[2]
            if len(year) == 4:
                return datetime.datetime.strptime(date, "[%d/%m/%Y").strftime("%Y-%m-%d")
            if len(year) == 2:
                return datetime.datetime.strptime(date, "[%d/%m/%y").strftime("%Y-%m-%d")