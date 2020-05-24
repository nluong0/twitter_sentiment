
import re
import string
import nltk
import pandas as pd
from nltk.stem.porter import PorterStemmer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
nltk.download('vader_lexicon')
nltk.download('stopwords')


class Classifier():
    '''
    Predict fine-grained sentiment classes using Vader.
    '''
    
    def __init__(self, df):
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        self.classifier = SentimentIntensityAnalyzer()
        self.scored_df = self.score_test_data(df)

    def score(self, tweet_text):
        return self.classifier.polarity_scores(tweet_text)['compound']

    def process_tweet(self, tweet):
        '''
        Processes tweets and creates a column for cleaned tweets in the 
        dataframe.
            (i) removes non-pertinent words (stopwords)
            (ii) removes strings representing twitter handles, links, and web pages
            (iii) removes punctuation and special characters
            (iv) converts all strings to lower case
            (v) normalizes strings to their stems 
        
        Inputs:
            tweet: (str)
        Output: 
            normalized: (str)
        '''
        stop_words = set(nltk.corpus.stopwords.words('english'))
        handles = r'@[A-Za-z0-9_]+'
        links = r'https?://[^ ]+'
        web_page = r'www.[^ ]+'

        remove_words = re.compile("(%s|%s|%s)" % (handles, links, web_page)).findall(tweet)
        for word in remove_words:
            tweet = tweet.replace(word, '')
        tweet = tweet.translate(str.maketrans('', '', string.punctuation))
        cleaned = [word.lower() for word in tweet.split() if word.lower() not in stop_words and word.lower().isalpha()]
        
        porter = PorterStemmer()
        normalized = []
        for word in cleaned:
            normalized.append(porter.stem(word))

        return ' '.join(normalized)

    def score_test_data(self, df):
        df['ProcessedTweet'] = df['TweetText'].apply(self.process_tweet)
        df['Score'] = df['ProcessedTweet'].apply(self.score)
        df['Score_bins'] = pd.cut(df['Score'], bins=5, labels= \
            ['Strongly Negative', 'Negative', 'Neutral', 'Positive', \
            'Strongly Positive']) 
        return df
    
