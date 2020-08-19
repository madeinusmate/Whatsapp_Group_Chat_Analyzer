from datetime import datetime
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from wordcloud import WordCloud
from Services import Services
from streamlit_echarts import st_echarts
from collections import Counter
from stop_words import get_stop_words


st.set_option('deprecation.showfileUploaderEncoding', False)



reset=st.sidebar.button("New Analysis")

st.sidebar.subheader("Upload your Whatsapp Chat File")
chat_file = st.sidebar.file_uploader("File must be .txt format", type="txt")

if reset:
    chat_file= None
#DATA TRANSFORMATION


if chat_file == None:
    st.header("Welcome to the Whatsapp Chat Analyzer")
    st.write("This app allows you to analyze your WhatsApp Group Chats - follow the steps below to start the analysis👇")

    st.subheader("Step 1")
    st.write("Open the Sidebar on the left side of the screen👈")

    st.subheader("Step 2")
    st.write("Upload your Whatsapp Chat File using the file uploader located in the sidebar📦")

    st.subheader("Step 3")
    st.write("Please type the name of your Whatsapp chat in input field located in the sidebar✍️")

    st.subheader("Step 4")
    st.write("HAVE FUN!😃")

else:
    line=chat_file.readline()
    line=line.strip()
    if (Services.startsWithDateAndTimeAndroid(line)==False) and (Services.startsWithDateAndTimeios(line)==False):
        st.subheader("Warning: The file provided is not correct!⚠️")
        st.write("Please follow the instruction located in the sidebar to extract your Whatsapp chat export from the app and upload the correct file.")

    else:
        @st.cache(allow_output_mutation=True)
        @st.cache
        def transform_data(chat_file):
            URLPATTERN = r'(https?://\S+)'

            parsedData = []

            device = ''
            first = chat_file.readline()
            if '[' in first:
                device = 'ios'
            else:
                device = "android"
            chat_file.readline()
            messageBuffer = []
            date, time, author = None, None, None
            while True:
                line = chat_file.readline()
                if not line:
                    break
                if device == "ios":
                    line = line.strip()
                    if Services.startsWithDateAndTimeios(line):
                        if len(messageBuffer) > 0:
                            parsedData.append([date, time, author, ' '.join(messageBuffer)])
                        messageBuffer.clear()
                        date, time, author, message = Services.getDataPointios(line)
                        messageBuffer.append(message)
                    else:
                        line = (line.encode('ascii', 'ignore')).decode("utf-8")
                        if Services.startsWithDateAndTimeios(line):
                            if len(messageBuffer) > 0:
                                parsedData.append([date, time, author, ' '.join(messageBuffer)])
                            messageBuffer.clear()
                            date, time, author, message = Services.getDataPointios(line)
                            messageBuffer.append(message)
                        else:
                            messageBuffer.append(line)
                else:
                    line = line.strip()
                    if Services.startsWithDateAndTimeAndroid(line):
                        if len(messageBuffer) > 0:
                            parsedData.append([date, time, author, ' '.join(messageBuffer)])
                        messageBuffer.clear()
                        date, time, author, message = Services.getDataPointAndroid(line)
                        messageBuffer.append(message)
                    else:
                        messageBuffer.append(line)

            if device == 'android':
                df = pd.DataFrame(parsedData, columns=['Date', 'Time', 'Author', 'Message'])
                df["Date"] = pd.to_datetime(df["Date"])
                df = df.dropna()
                df["emoji"] = df["Message"].apply(Services.split_count)
                URLPATTERN = r'(https?://\S+)'
                df['urlcount'] = df.Message.apply(lambda x: re.findall(URLPATTERN, x)).str.len()
            else:
                df = pd.DataFrame(parsedData, columns=['Date', 'Time', 'Author', 'Message'])
                df = df.dropna()
                df["Date"] = df["Date"].apply(Services.dateconv)
                df["Date"] = pd.to_datetime(df["Date"], format='%Y-%m-%d')
                df["emoji"] = df["Message"].apply(Services.split_count)
                URLPATTERN = r'(https?://\S+)'
                df['urlcount'] = df.Message.apply(lambda x: re.findall(URLPATTERN, x)).str.len()

            df["emoji"] = df["emoji"].apply(lambda x: "".join(sorted(set(x))))
            df = df[df["Author"].str.contains("added") == False]
            df = df[df["Author"].str.contains("left") == False]

            total_messages = df.shape[0]
            media_messages = df[df['Message'].str.contains("omitted") == True].shape[0]
            emojis = sum(df['emoji'].str.len())
            links = np.sum(df.urlcount)

            media_messages_df = df[df['Message'].str.contains("omitted") == True]
            messages_df = df.drop(media_messages_df.index)
            messages_df['Letter_Count'] = messages_df['Message'].apply(lambda s: len(s))
            messages_df['Word_Count'] = messages_df['Message'].apply(lambda s: len(s.split(' ')))

            l = messages_df.Author.unique()
            Members = pd.DataFrame(l, columns=['Author'])
            Members=Members.append({"Author" : "All"}, ignore_index=True)
            Members["new"] = range(1,len(Members)+1)
            Members['new'].replace((len(Members)+1),0,inplace=True)
            Members.loc[Members["Author"]=="All", "new"] = 0
            Members=Members.sort_values("new").reset_index(drop='True').drop('new', axis=1)
            l = Members.Author.unique()

            return l, Members, messages_df, media_messages_df, total_messages, media_messages, emojis, links, device

        l, Members, messages_df, media_messages_df, total_messages, media_messages, emojis, links, device=transform_data(chat_file)

        chat_language=st.sidebar.selectbox("What's your chat language?", ("-","Italian", "English"))
        chat_name=st.sidebar.text_input("What's your chat Name?", "")
        if chat_language=="-":
            st.subheader("⚠️ Warning: Chat Language Missing. ⚠️")
            st.write("Please select the language of your chat in the sidebar")
        if chat_name=="":
            st.subheader("⚠️ Warning: Chat Name Missing. ⚠️")
            st.write("Please type the name of your chat in the sidebar")
        else:
            st.title(chat_name + " - Chat Analysis")


            st.markdown("---")


            #WIDGETS
            today = datetime.today()
            day = today.day
            month = today.month
            year = today.year
            chat_start = messages_df.iloc[0][0]
            chat_start_day = chat_start.day
            chat_start_month = chat_start.month
            chat_start_year = chat_start.year

            time_frame = st.slider("Select Analysis Timeframe",format="DD/MM/YYYY", min_value=datetime(chat_start_year, chat_start_month, chat_start_day), max_value=datetime(year, month, day), value=(datetime(chat_start_year, chat_start_month, chat_start_day),datetime(year, month, day)))
            time_frame = pd.Series(time_frame).astype(int)
            time_frame_min= time_frame.iloc[0]
            time_frame_max = time_frame.iloc[1]

            timefilter_messages_df=messages_df
            timefilter_messages_df["time_filter"] = timefilter_messages_df["Date"].astype(int)

            timefilter_messages_df=timefilter_messages_df[timefilter_messages_df["time_filter"] >= time_frame_min]
            timefilter_messages_df=timefilter_messages_df[timefilter_messages_df["time_filter"] <= time_frame_max]

            timefilter_media_messages_df=media_messages_df
            timefilter_media_messages_df["time_filter"] = timefilter_media_messages_df["Date"].astype(int)
            timefilter_media_messages_df = timefilter_media_messages_df[timefilter_media_messages_df["time_filter"] > time_frame_min]
            timefilter_media_messages_df = timefilter_media_messages_df[timefilter_media_messages_df["time_filter"] < time_frame_max]


            selection=st.selectbox(
                'Select Chat Member',
                Members.Author.unique())

            if selection=="All":
                req_df=timefilter_messages_df
                media = timefilter_media_messages_df

            else:
                i = Members[Members["Author"] == selection].first_valid_index()
                req_df = timefilter_messages_df[timefilter_messages_df["Author"] == l[i]]
                media = timefilter_media_messages_df[timefilter_media_messages_df['Author'] == l[i]]


            #General STATS

            st.markdown("---")

            if req_df.shape[0]== 0:
                st.subheader("⚠️ Warning ⚠️")
                st.markdown("No messages have been sent in the selected timeframe. Please change the analysis timeframe using the slider above ⏱")
            else:


                avg_words_per_message = int((np.sum(req_df['Word_Count']))/req_df.shape[0])
                avg_letters_per_message = int((np.sum(req_df['Letter_Count']))/req_df.shape[0])
                emojis = sum(req_df['emoji'].str.len())
                links = sum(req_df["urlcount"])
                active_days=req_df["Date"].unique().shape[0]
                avg_message_per_day=int((req_df.shape[0]/active_days))
                most_active_day=req_df["Date"].value_counts().reset_index().iloc[0,0]
                most_active_day =pd.Series(most_active_day)
                most_active_day=most_active_day.dt.strftime("%A %d %B %Y")

                st.subheader('Total Messages Sent: '+ str(req_df.shape[0]))
                st.subheader('Total Words Sent; ' + str(np.sum(req_df['Word_Count'])))
                st.subheader('Total Letters Sent; '+ str(np.sum(req_df['Letter_Count'])))
                st.subheader('Most Active Day: '+ str(most_active_day[0]))
                st.subheader('Media Sent: '+ str(media.shape[0]))
                st.subheader('Emojis Sent: '+ str(emojis))
                st.subheader('Links Sent: '+ str(links))
                st.subheader('Total Active Days: '+ str(active_days))


                st.subheader('Average Messages per Day: '+ str(avg_message_per_day))
                st.subheader('Average Words per Message: '+ str(avg_words_per_message))
                st.subheader('Average Letters per Message: '+ str(avg_letters_per_message))



                #Members Breakdown

                if selection=="All":
                    members_breakdown_df=timefilter_messages_df["Author"].value_counts()
                    members_breakdown_df=pd.DataFrame(members_breakdown_df)
                    members_breakdown_df.reset_index(inplace=True)
                    members_breakdown_df.columns=["Author", "Message Count"]


                    members_breakdown_options = {
                        "title": {
                            "text": 'Top Contributors',
                            "left": "center",
                        },
                        "tooltip": {
                            "trigger": "axis",
                            "axisPointer": {"type": "shadow"},
                        },
                        "grid": {
                            "bottom": "90",
                        "left": "20%"},
                        "xAxis": [
                            {
                                "name" : "Messages Sent",
                                "show": "false",
                                "type": "value",
                            },

                        ],
                        "yAxis": [
                            {
                                "type": "category",
                                "inverse" : "true",
                                "data": members_breakdown_df["Author"].values.tolist(),
                                "axisPointer": {"type": "shadow"},
                                "show": "true",
                                "axisLabel": {
                                    "interval": 0
                                },
                            },
                        ],
                        "series": [
                            {
                                "name": "Count",
                                "type": "bar",

                                "large": "false",
                                "data": members_breakdown_df["Message Count"].values.tolist(),
                            },
                        ],
                    }
                    st.markdown("---")
                    st_echarts(members_breakdown_options)

                #WORDCLOUD

                @st.cache
                def generate_stopwords():
                    stopwords_ita = set(get_stop_words('italian'))

                    stopwords_eng = set(get_stop_words('english'))

                    if chat_language=="English":
                        stopwords=stopwords_eng
                    if chat_language=="Italian":
                        stopwords=stopwords_ita

                    return stopwords

                stopwords=generate_stopwords()

                text = " ".join(review for review in req_df.Message)
                wordcloud = WordCloud(stopwords=stopwords, background_color="white").generate(text)
                plt.figure(figsize=(7, 5))
                plt.title("Most Used Words")
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis("off")
                word_cloud=plt.show()
                st.markdown("---")

                st.pyplot(word_cloud)

                #TimelineCHART

                timeline_df = req_df.groupby("Date").sum()
                timeline_df["Message_Count"]=req_df['Date'].value_counts()
                timeline_df.reset_index(inplace=True)
                timeline_df["Date"]=timeline_df["Date"].dt.strftime('%d/%m/%Y')




                timeline_options = {
                    "title": {
                        "text": 'Interactions by Day',
                        "left": "center",
                        },
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {"type": "shadow"},
                    },
                    "grid": {
                        "bottom": "90"},
                    "toolbox": {
                        "feature": {
                            "dataZoom": {
                                "yAxisIndex": "true"
                                        },
                                    },
                                },
                    "xAxis": [
                        {
                        "type": "category",
                        "data": timeline_df["Date"].values.tolist(),
                        "axisPointer": {"type": "shadow"},
                        "show": "false",
                        },
                    ],
                    "yAxis": [
                        {

                            "type": "value",
                            "name": "Messages",
                            "min": 0,
                            "position" : "top",
                        },
                    ],
                    "dataZoom": [{
                        "type": 'inside'
                    }, {
                        "type": 'slider'
                    }],
                    "series": [
                        {
                            "name": "Messages",
                            "type": "bar",
                            "large" : "true",
                            "data": timeline_df["Message_Count"].values.tolist(),
                            "seriesLayoutBy": 'row',
                        },
                    ],
                }
                st.markdown("---")
                st_echarts(timeline_options)



                #Media breakdown

                if device == 'android':
                    pass
                else:
                    media_breakdown_df=media["Message"].value_counts()
                    media_breakdown_df=pd.DataFrame(media_breakdown_df)
                    media_breakdown_df.reset_index(inplace=True)
                    media_breakdown_df['index'] = media_breakdown_df['index'].str.replace(' omitted','')
                    media_breakdown_df['index'] = media_breakdown_df['index'].str.replace('image','Image')
                    media_breakdown_df['index'] = media_breakdown_df['index'].str.replace('video','Video')
                    media_breakdown_df['index'] = media_breakdown_df['index'].str.replace('audio','Audio')
                    media_breakdown_df['index'] = media_breakdown_df['index'].str.replace('sticker','Sticker')
                    media_breakdown_df['index'] = media_breakdown_df['index'].str.replace(r'[\s\S]*(document)[\s\S]*','PDF',regex=True)
                    media_breakdown_df=media_breakdown_df.groupby("index").sum()
                    media_breakdown_df.reset_index(inplace=True)
                    media_breakdown_df.columns=["Media Type", "Count"]
                    media_breakdown_df.sort_values('Count',inplace=True, ascending=False)



                    media_breakdown_options = {
                        "title": {
                            "text": 'Media Sent Breakdown',
                            "left": "center",
                            },
                        "tooltip": {
                            "trigger": "axis",
                            "axisPointer": {"type": "shadow"},
                        },
                        "grid": {
                            "bottom": "90"},
                        "xAxis": [
                            {
                            "type": "category",
                            "data": media_breakdown_df["Media Type"].values.tolist(),
                            "axisPointer": {"type": "shadow"},
                            "show": "True",
                            "axisLabel": {
                                "interval": 0
                        },
                            },
                        ],
                        "yAxis": [
                            {
                                "show" : "false",
                                "type": "value",
                            },
                        ],
                        "series": [
                            {
                                "name": "Count",
                                "type": "bar",
                                "large" : "false",
                                "data": media_breakdown_df["Count"].values.tolist(),
                            },
                        ],
                    }
                    st.markdown("---")
                    st_echarts(media_breakdown_options)




                #Emoji Breakdown



                total_emojis_list = list([a for b in req_df.emoji for a in b])
                emoji_dict = dict(Counter(total_emojis_list))
                emoji_dict = sorted(emoji_dict.items(), key=lambda x: x[1], reverse=True)
                emoji_df = pd.DataFrame(emoji_dict, columns=['Emoji', 'Count']).head(25)

                emoji_options = {
                    "title": {
                        "text": 'Top 25 Emojis',
                        "left": "center",
                        },
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {"type": "shadow"},
                    },
                    "grid": {
                        "bottom": "90"},
                    "xAxis": [
                        {
                        "type": "category",
                        "data": emoji_df["Emoji"].values.tolist(),
                        "axisPointer": {"type": "shadow"},
                        "axisLabel": {
                                "interval": 0
                            },
                        },
                    ],
                    "yAxis": [
                        {
                            "type": "value",
                            "name": "Count",
                            "min": 0,
                            "position" : "top",
                        },
                    ],
                    "series": [
                        {
                            "name": "Count",
                            "type": "bar",
                            "data": emoji_df["Count"].values.tolist(),
                        },
                    ],
                }
                st.markdown("---")
                st_echarts(emoji_options)


                #RADAR - Activity by Time of the Day

                hour_rank={'12 PM': 0, '11 AM':1, '10 AM':2, '9 AM':3, '8 AM':4,'7 AM':5,'6 AM':6,'5 AM':7,'4 AM':8,'3 AM':9,'2 AM':10,'1 AM':11,'12 AM':12,'11 PM':13,'10 PM':14,'9 PM':15,'8 PM':16,'7 PM':17,'6 PM':18,'5 PM':19,'4 PM':20,'3 PM':21,'2 PM':22,'1 PM':23}
                hour_series={"Time" : ['12 PM', '11 AM', '10 AM', '9 AM', '8 AM','7 AM','6 AM','5 AM','4 AM','3 AM','2 AM','1 AM','12 AM','11 PM','10 PM','9 PM','8 PM','7 PM','6 PM','5 PM','4 PM','3 PM','2 PM','1 PM']}
                hour=pd.DataFrame(hour_series)

                messages_radar_df=req_df
                messages_radar_df=messages_radar_df.drop("time_filter", axis=1)
                if device== "android":
                    messages_radar_df["Time"]=pd.to_datetime(messages_radar_df["Time"])
                    messages_radar_df["Time"]=messages_radar_df["Time"].dt.strftime("%I %p")

                if device == "ios":
                    messages_radar_df["Time"].replace(to_replace=r'[\D]*:[\s\S]*AM', value=" AM", regex=True, inplace=True)
                    messages_radar_df["Time"].replace(to_replace=r'[\D]*:[\s\S]*PM', value=" PM", regex=True, inplace=True)

                messages_radar_df["Time"]=messages_radar_df["Time"].astype(str)
                for i in range (0,messages_radar_df["Time"].shape[0]):
                    string=messages_radar_df["Time"].iloc[i]
                    first_char=string[0]
                    if first_char == "0":
                        messages_radar_df["Time"].replace(to_replace=r'^0', value="", regex=True, inplace=True)

                messages_radar_df["Time"]=messages_radar_df['Time'].str.strip()
                messages_radar_df["Message_Count"]=1
                messages_radar_df=messages_radar_df.groupby("Time").sum()
                messages_radar_df=messages_radar_df.reset_index()

                if messages_radar_df.shape[0] < 24:
                    for x in range(24-messages_radar_df.shape[0]):
                        s1 = pd.Series([None,0, 0, 0, 0], index=["Time",'urlcount', 'Letter_Count', 'Word_Count', 'Message_Count'])
                        messages_radar_df = messages_radar_df.append(s1, ignore_index=True)
                        dummy_time= messages_radar_df.Time
                        dummy_time=dummy_time.append(hour["Time"],ignore_index=True)
                        dummy_time=dummy_time.drop_duplicates(keep="first")
                        dummy_time = dummy_time.dropna()
                        dummy_time = dummy_time.reset_index(drop=True)
                        messages_radar_df["Time"]=dummy_time
                messages_radar_df['rank'] =messages_radar_df['Time'].str.strip().map(hour_rank)

                messages_radar_df['rank']=messages_radar_df["rank"].astype(int)
                messages_radar_df.sort_values('rank',inplace=True)
                messages_radar_df.set_index('rank', inplace=True, drop=True)
                max = messages_radar_df["Message_Count"].max()
                max=max.item()



                media_radar_df=media

                media_radar_df = media_radar_df.drop("time_filter", axis=1)
                if device == "android":
                    media_radar_df["Time"] = pd.to_datetime(media_radar_df["Time"])
                    media_radar_df["Time"] = media_radar_df["Time"].dt.strftime("%I %p")

                if device == "ios":
                    media_radar_df["Time"].replace(to_replace=r'[\D]*:[\s\S]*AM', value=" AM", regex=True,inplace=True)
                    media_radar_df["Time"].replace(to_replace=r'[\D]*:[\s\S]*PM', value=" PM", regex=True, inplace=True)

                media_radar_df["Time"] = media_radar_df["Time"].astype(str)
                for i in range(0, media_radar_df["Time"].shape[0]):
                    string = media_radar_df["Time"].iloc[i]
                    first_char = string[0]
                    if first_char == "0":
                        media_radar_df["Time"].replace(to_replace=r'^0', value="", regex=True, inplace=True)
                media_radar_df["Time"]=media_radar_df['Time'].str.strip()
                media_radar_df["Media_Count"]=1
                media_radar_df=media_radar_df.groupby("Time").sum().drop("urlcount", axis=1)
                media_radar_df=media_radar_df.reset_index()

                if media_radar_df.shape[0] < 24:
                    for x in range(24-media_radar_df.shape[0]):
                        s1 = pd.Series([None, 0], index=["Time", 'Media_Count'])
                        media_radar_df = media_radar_df.append(s1, ignore_index=True)
                        dummy_time= media_radar_df.Time
                        dummy_time=dummy_time.append(hour["Time"],ignore_index=True)
                        dummy_time=dummy_time.drop_duplicates(keep="first")
                        dummy_time = dummy_time.dropna()
                        dummy_time = dummy_time.reset_index(drop=True)
                        media_radar_df["Time"]=dummy_time
                media_radar_df['rank'] =media_radar_df['Time'].str.strip().map(hour_rank)
                media_radar_df['rank']=media_radar_df["rank"].astype(int)
                media_radar_df.sort_values('rank',inplace=True)
                media_radar_df.set_index('rank', inplace=True, drop=True)
                max_media=media_radar_df["Media_Count"].max()
                max_media = max_media.item()


                option_radar_message= {
                    "title": {
                        "text": 'Activity by Time of the Day',
                        "left": "center",
                    },
                    "tooltip": {
                        "confine" : "true",
                        "position": ["90%", "10"],
                        "textStyle" : {
                            "fontSize" : 12
                        },
                    },
                    "legend": {
                        "data": ['Messages Sent'],
                        "left": "left",
                        "top": "7%",
                        "type" : "plain",
                        "orient" : "vertical",
                    },
                    "radar": {
                        "shape": 'circle',
                        "splitNumber" : 6,
                        "center": ["50%", "55%"],
                        "startAngle" : 90,
                        "radius": '70%',
                        "scale" : "true",
                        "splitArea": {
                            "show": "true",
                            "areaStyle": {
                                "color" : 'rgba(0,0,0,0)'
                                    },
                        },
                        "axisLine": {
                            "show": "true",
                            "lineStyle": {
                                "color": 'rgba(0,0,0,0.1)'
                            },
                        },
                        "splitLine": {
                                    "show": "true",
                                    "lineStyle": {
                                        "color" : 'rgba(0,0,0,0.1)'
                                            },
                        },
                        "name": {
                            "textStyle": {
                                "color": '#fff',
                                "backgroundColor": '#999',
                                "borderRadius": 3,
                                "padding": [3, 5]
                            },
                        },
                        "indicator": [

                            {"name": '12 PM', "max" : max},
                            {"name": '11 AM', "max" : max},
                            {"name": '10 AM', "max" : max},
                            {"name": '9 AM', "max" : max},
                            {"name": '8 AM', "max" : max},
                            {"name": '7 AM', "max" : max},
                            {"name": '6 AM', "max" : max},
                            {"name": '5 AM', "max" : max},
                            {"name": '4 AM', "max" : max},
                            {"name": '3 AM', "max" : max},
                            {"name": '2 AM', "max" : max},
                            {"name": '1 AM', "max" : max},
                            {"name": '12 AM', "max" : max},
                            {"name": '11 PM', "max" : max},
                            {"name": '10 PM', "max" : max},
                            {"name": '9 PM', "max" : max},
                            {"name": '8 PM', "max" : max},
                            {"name": '7 PM', "max" : max},
                            {"name": '6 PM', "max" : max},
                            {"name": '5 PM', "max" : max},
                            {"name": '4 PM', "max" : max},
                            {"name": '3 PM', "max" : max},
                            {"name": '2 PM', "max" : max},
                            {"name": '1 PM', "max" : max},
                        ],
                    },
                    "series": [{
                        "type": 'radar',
                        "areaStyle": {
                                "color": "rgba(0, 0, 0, 0)"
                        },
                        "data": [
                            {
                                "value": messages_radar_df.Message_Count.to_list(),
                                "name": 'Messages Sent',
                            },

                        ],
                },
                ],
                }
                st.markdown("---")

                st_echarts(option_radar_message)

                option_radar_media= {

                    "tooltip": {
                        "confine" : "true",
                        "position": ["90%", "10"],
                        "textStyle" : {
                            "fontSize" : 12
                        },
                    },
                    "legend": {
                        "data": ['Media Sent'],
                        "left": "left",
                        "top": "7%",
                        "type" : "plain",
                        "orient" : "vertical",
                    },
                    "radar": {
                        "shape": 'circle',
                        "splitNumber" : 6,
                        "center": ["50%", "55%"],
                        "startAngle" : 90,
                        "radius": '70%',
                        "scale" : "true",
                        "splitArea": {
                            "show": "true",
                            "areaStyle": {
                                "color" : 'rgba(0,0,0,0)'
                                    },
                        },
                        "axisLine": {
                            "show": "true",
                            "lineStyle": {
                                "color": 'rgba(0,0,0,0.1)'
                            },
                        },
                        "splitLine": {
                                    "show": "true",
                                    "lineStyle": {
                                        "color" : 'rgba(0,0,0,0.1)'
                                            },
                        },
                        "name": {
                            "textStyle": {
                                "color": '#fff',
                                "backgroundColor": '#999',
                                "borderRadius": 3,
                                "padding": [3, 5]
                            },
                        },
                        "indicator": [

                            {"name": '12 PM', "max" : max_media},
                            {"name": '11 AM', "max" : max_media},
                            {"name": '10 AM', "max" : max_media},
                            {"name": '9 AM', "max" : max_media},
                            {"name": '8 AM', "max" : max_media},
                            {"name": '7 AM', "max" : max_media},
                            {"name": '6 AM', "max" : max_media},
                            {"name": '5 AM', "max" : max_media},
                            {"name": '4 AM', "max" : max_media},
                            {"name": '3 AM', "max" : max_media},
                            {"name": '2 AM', "max" : max_media},
                            {"name": '1 AM', "max" : max_media},
                            {"name": '12 AM', "max" : max_media},
                            {"name": '11 PM', "max" : max_media},
                            {"name": '10 PM', "max" : max_media},
                            {"name": '9 PM', "max" : max_media},
                            {"name": '8 PM', "max" : max_media},
                            {"name": '7 PM', "max" : max_media},
                            {"name": '6 PM', "max" : max_media},
                            {"name": '5 PM', "max" : max_media},
                            {"name": '4 PM', "max" : max_media},
                            {"name": '3 PM', "max" : max_media},
                            {"name": '2 PM', "max" : max_media},
                            {"name": '1 PM', "max" : max_media},
                        ],
                    },
                    "series": [{
                        "type": 'radar',
                        "animation" : "true",
                        "areaStyle": {
                                "color": "rgba(0, 0, 0, 0)"
                        },
                        "data": [
                            {
                                "value": media_radar_df.Media_Count.to_list(),
                                "name": 'Media Sent',
                            },

                        ],
                },
                ],
                }

                st_echarts(option_radar_media)


st.sidebar.markdown("---")


st.sidebar.subheader('**FAQs**')
st.sidebar.markdown('**How to export chat text file? (Not Available on Whatsapp Web)**')
st.sidebar.markdown('Follow the steps 👇:')
st.sidebar.markdown('1) Open the individual or group chat.')
st.sidebar.markdown('2) Tap options > More > Export chat.')
st.sidebar.markdown('3) Choose export without media.')
st.sidebar.markdown('4) Unzip the file and you are all set to go 😃.')
st.sidebar.markdown('**What happens to my data?**')
st.sidebar.markdown('The data you upload is not saved anywhere on this site or any 3rd party site i.e, not in any storage like DB/FileSystem/Logs.')
st.sidebar.markdown('**What mobile OS are supported?**')
st.sidebar.markdown('Both iOS and Android are supported.')
st.sidebar.markdown('**What languages are supported?**')
st.sidebar.markdown('🇬🇧 English  \n🇮🇹 Italian')

st.sidebar.markdown("---")


st.sidebar.markdown("Made with ❤️ by [![Stefano Cantù]\
                    (https://img.shields.io/badge/Author-%40StefanoCant%C3%B9-blue)]\
                    (https://github.com/settings/profile)")



