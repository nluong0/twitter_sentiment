#import time
#import datetime
import pandas as pd
import tweepy as tw
from analyze import TweetData

consumer_key = "H4Fwzo2sWBTW3DrWCkX0GvlLi"
consumer_secret = "IIyP5LMbGqLrgsFS6Ljjx9y69K7w4x8Z29uXmNt7OYaAK2PSuv"
access_token = "1225451977829691395-kCSE323X79bHRA1JRNk5o5SRhgMh2N"
access_token_secret = "ztkDGiMMq1DymO6yEN863RzUCRihNW5DXSMdNBhd5OP2A"

auth = tw.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tw.API(auth, wait_on_rate_limit_notify=True)

pres_candidates = {"@BernieSanders":["Bernie", "Sanders"],
                   "@JoeBiden":["Biden"],
                   "@realDonaldTrump":["Trump"]}

cities = pd.read_csv("uscities.csv")


def get_candidate_friends(user_id, candidate_ids):
    '''
    Gets mutual follow relationships.

    Inputs: 
        user_id: (str of ints) user who tweeted
        candidate_ids: (list) candidate user_ids
    Outputs: 
        (list of bool) whether or not user is following candidate at same index in candidate_ids
    '''
    try:
        friends = [api.show_friendship(source_id=user_id, target_id=c)[1].followed_by for c in candidate_ids] 
    except:
        friends = [None] * len(candidate_ids)
    return friends


def get_geocode(city, state, radius):
    '''
    Gets the geocode of a location.

    Inputs: 
        city: (str)
        state: (str) state abbreviation
        radius: (int) in miles 
    Outputs:
        (str) of latitiude, longitude, and radius or None
    '''
    city = cities.loc[(cities["city"] == city) & (cities["state_id"] == state)]
    if city.empty:
        return None
    return "{},{},{}".format(city.lat.values[0], city.lng.values[0], str(radius) + "mi")


def search_tweets(search_word, loc, tweets_to_pull=150, result_type='recent',
                  candidates=None):
    '''
    Gathers testing data tweets according to parameters.

    Inputs:
        search_word: (str)
        loc: (dict) where keys are 'city', 'state', and 'radius'
        step: (int) tweet limit set at 150
        result_type: (str)
        candidates: (dict) set to pres_candidates 
    Outputs:
        TweetData object
    '''
    if not candidates:
        candidates = pres_candidates
    geocode = get_geocode(loc["city"], loc["state"], loc["radius"])
    if not geocode:
        return None
    search_params = locals()
    candidate_ids = [api.get_user(screen_name=sn).id for sn in candidates.keys()]

    columns = ["TweetText", "user_id", "User Location", "Time Searched",
               "Favorite Count", "Retweet Count"] + \
               ["Follows " + k for k in candidates.keys()]

    data = []
    cursor = tw.Cursor(api.search,
                       q=search_word + ' -filter:retweets',
                       geocode=geocode,
                       lang="en",
                       result_type=result_type,
                       tweet_mode="extended").items(tweets_to_pull)
    for t in cursor:
        candidate_friends = get_candidate_friends(t.user.id, candidate_ids)
        row = [t.full_text, t.user.id, t.user.location, t.created_at, \
               t.favorite_count, t.retweet_count] + candidate_friends
        data.append(row)

    tweets_df = pd.DataFrame(data, columns=columns)
    tweets_df.to_csv('test_data.csv')

    return TweetData(tweets_df, search_params)


    '''
    Alt Idea
    - Allow user to input an entity (news outlet, public figure, local gov officials, state)
    - Check to see if that entity has a twitter account
    - Pull all tweets from that account's timeline (potentially with a keyword --would be in
      analyze.py with work through strings instead of with twitter api in this .py file)
    - Analyze those tweets 

    Could answer questions similar to ones below.
        - What does the NYT or WashPo tweets about the most?
        - What is a mayor's most successful tweet?
        - Which states are tweeting about a certain event most positively/most negatively?

    data = []
    name = "nytimes"
    num_tweets = 150
    results = api.user_timeline(id=name, count=num_tweets)
    For tweet in results:
        data.append(tweet.text)
    df = pd.DataFrame(data, columns=['tweet_text'])
    '''
    
