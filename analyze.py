from classifier import Classifier
from itertools import permutations


class TweetData():
    '''
    Class representing dataset of tweets and search parameters.
    '''

    def __init__(self, df, search_params, update_flags=None):
        '''
        Inputs: 
            df: (pandas.DataFrame) of tweets
            search params: (dict) parameters of search from ui
            update flag: (list of str) identifier of historical data topic
        '''
        self.query = search_params["search_word"]
        self.data = Classifier(df).scored_df.sort_values(['Score'])
        if not hasattr(self, "candidates"):
            self.candidates = search_params["candidates"]
        self.geocode = search_params["geocode"]
        self.result_type = search_params["result_type"]
        self.big_summary = self.data["Score"].describe()

    def calc_stats(self, handle, col_string):
        '''
        Calculate basic descriptive statistics for any given subset of the data. 
        These statistics include: a five-number summary, difference in mean
        sentiment score between subset and whole dataset, three most positive tweets,
        three most negative tweets, and three most neutral tweets.

        Inputs:
            handle: (str or tuple) str of candidate handle of tuple of 
                                  two candidate handles
            col_string (str): either 'Follows ' or 'Mentions '
        Outputs:
            (list) of all the aforementioned statistics
        '''
        mean_score = self.data['Score'].describe()['mean']
   
        if isinstance(handle, tuple):
            cand1, cand2 = handle
            filtered = self.data[(self.data['Follows ' + cand1] == True) &
                                 (self.data['Mentions ' + cand2] == True)]
        else:
            filtered = self.data[self.data[col_string + handle] == True]
        if len(filtered) < 5:
            return None

        filtered_summary = filtered['Score'].describe().to_string()
        mean = filtered['Score'].describe()['mean']
        mean_diff = str(mean_score - mean)
        tweet_pos, tweet_neg, tweet_med = self.find_pos_neg_medium_tweets(filtered)

        return [filtered_summary, mean_diff, tweet_pos, tweet_neg, tweet_med]

    def find_pos_neg_medium_tweets(self, df):
        '''
        Finds the most positive, negative, and netural tweets in the data.

        Inputs:
            df (pandas.DataFrame)
        Outputs:
            (str) 3 correctly formatted strings of tweets to be displayed by ui
        '''
        med = df['Score'].median()
        pos_tweets = df.tail(3)['TweetText']
        neg_tweets = df.head(3)['TweetText']
        med_tweets = df[df['Score'] == med].head(3)['TweetText']
        return self.format_strings(pos_tweets), self.format_strings(neg_tweets), self.format_strings(med_tweets)

    def format_strings(self, tweet_series):
        '''
        Formats strings of 3 most positive, negative, and neutral tweets appropriately. Used as 
        a helper function to find_pos_neg_medium_tweets().

        Inputs:
            tweet_series: (pandas.Series) series of tweets
        Outputs:
            (str) of number and tweet text
        '''
        rv = ''
        for i, text in enumerate(tweet_series):
            rv += 'Tweet {}: {} \n'.format(i+1, text)
        return rv

    def summarize_sentiment(self, col_string):
        '''
        Summarizes sentiment by follows or mentions depending on col_string.

        Inputs:
            col_string: (str) either 'Follows ' or 'Mentions '
        Outputs:
            (str) of summary to be displayed by ui
        '''
        handle_list = self.candidates.keys()
        rv = ''
        init_length = len(rv)
        for handle in handle_list:
            stats = self.calc_stats(handle, col_string)
            if stats:
                rv += """Summary of tweets from followers of {}.
                         {}
                         Average tweet is {} more positive than the average tweet pulled.

                         3 most positive tweets:
                         {}

                         3 most negative tweets:
                         {}

                         3 neutral tweets:
                         {}\n""".format(handle, stats[0], stats[1], stats[2], stats[3], stats[4])
        if len(rv) == init_length:
            rv += "Whoops! Fewer than 5 tweets meet these criteria."
        return rv

    def summarize_sentiment_by_followers_and_mentions(self):
        '''
        Summarizes sentiment for every permutation of two candidates.

        Outputs:
            (str) of summary to be displayed by ui
        '''
        handle_list = list(permutations(self.candidates.keys(), 2))
        rv = 'Summary of tweet sentiment by followers and mentions:\n'
        init_length = len(rv)
        for (cand1, cand2) in handle_list:
            stats = self.calc_stats((cand1, cand2), '')
            if stats:
                rv += """Summary of tweets from followers of {} and mentioning {}.
                         {}
                         Average tweet is {} more positive than the average tweet pulled.

                         3 most positive tweets:
                         {}

                         3 most negative tweets:
                         {}

                         3 neutral tweets:
                         {}\n""".format(cand1, cand2, stats[0], stats[1], stats[2], stats[3], stats[4])
        if len(rv) == init_length:
            rv += "Whoops! Fewer than 5 tweets meet these criteria."
        return rv

    def summarize_follow_data(self):
        '''
        Summarizes data on user follow behavior within dataset of tweets pulled.

        Outputs:
            (str) of summary to be displayed by ui
        '''
        rv = ""
        follower_column = None
        for c in range(self.data.shape[1]):
            if self.data.columns[c][0:7] == "Follows":
                follower_column = c
                break
        tweets_wf = self.data[self.data.iloc[:, c].isna() == False]
        rv += "Of the {} tweets {} have data on who user \
                is following\n".format(self.data.shape[0], tweets_wf.shape[0])
        while c < self.data.shape[1] and  self.data.columns[c][0:7] == "Follows":
            rv += "Of those {} tweets,\
                   {} follow {}\n".format(tweets_wf.shape[0], 
                                          tweets_wf.iloc[:, c].sum(), 
                                          self.data.columns[c][7:])
            c += 1
        return rv

    def summarize_tweets_ab_candidates(self, other_candidates={}):
        '''
        Summarizes tag and mention behavior of tweets in the dataset.

        Outputs:
            (str) of summary to be displayed by ui
        '''
        rv = ""
        candidate_dict = self.candidates.copy()
        candidate_dict.update(other_candidates)

        candidate_names = []
        [candidate_names.extend(name+[k]) for k, name in self.candidates.items()]

        self.data["Mention or Tag any Candidate"] = None

        for c_n in candidate_names:
            self.data.loc[self.data["TweetText"].str.contains(c_n),
                          "Mention or Tag any Candidate"] = True

        count_that_mention = self.data["Mention or Tag any Candidate"].sum()
        rv += "Of the {} tweets gathered, {} ({} %) tag one of the candidates \
               or mention them by an \
               alias \n".format(self.data.shape[0],
                                count_that_mention,
                                (count_that_mention/self.data.shape[0])*100)


        for handle, aliases in candidate_dict.items():

            self.data["Tags " + handle] = self.data["TweetText"].str.contains(handle)

            self.data["Mentions " + handle] = False
            for a in [handle] + aliases:
                self.data.loc[self.data["TweetText"].str.contains(a),
                              "Mentions " + handle] = True
            

            rv += "Of the {} tweets that mention any candidate, \
                  {} ({} %) mention {} \
                  \n".format(self.data["Mention or Tag any Candidate"].sum(),
                             self.data["Mentions " + handle].sum(),
                             (self.data["Mentions " + handle].sum()/count_that_mention)*100,
                             handle)
        return rv
    
    def update_handler(self, df, update_flags, search_params):
        '''
        In the case of using historical data (housed in csv files), makes the necessary
        changes to the csv files for processing data in the same manner as real-time
        data pull with search parameters.

        Inputs:
            df: (pandas.DataFrame) contents of csv files
            update_flags: (list of str) identifier of historical data topic
            search_params: (dict) search parameters of historical data
        '''
        if "Super Tuesday" in update_flags:
            self.candidates = {"@BernieSanders":["Bernie", "Sanders"],
                               "@ewarren":["Warren"],
                               "@MikeBloomberg": ["Bloomberg"],
                               "@JoeBiden":["Biden"]}
            df.rename(columns={"FollowsSanders":"Follows @BernieSanders",
                               "FollowsWarren": "Follows @ewarren",
                               "FollowsBloomberg": "Follows @MikeBloomberg",
                               "FollowsBiden": "Follows @JoeBiden",
                               "Tweet Text": "TweetText"}, inplace=True)
        if "8Ver" in update_flags:
            df.rename(columns={"Tweet Text": "TweetText"}, inplace=True)
            self.query = search_params["q"]

    def __repr__(self):
        '''
        Displays search parameters and preview of data for a given TweetData object.
        '''
        return '''Search was conduced with the following parameters.
                  Search terms: {}
                  Geocode: {}
                  Result type: {}

                  Preview of resulting dataframe.
                  {}'''.format(self.query, self.geocode, self.result_type, self.data.head(10))
                  