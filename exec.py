'''
Flask documentation:
https://flask.palletsprojects.com/en/1.1.x/
Flask-WTF documentation:
https://flask-wtf.readthedocs.io/en/stable/
Jinja documentation:
https://jinja.palletsprojects.com/en/2.11.x/
'''
import flask
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional
from io import BytesIO
from matplotlib import pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
from search import search_tweets
import csv_to_tweets
import templates

class SearchForm(FlaskForm):
    '''
    Class representing search fields and search buttons.
    '''
    searchTerm = StringField('Search term (example: primary election)')
    cityTerm = StringField('City (example: New York)')
    stateTerm = StringField('State (example: NY)')
    radiusVal = IntegerField('Radius (example: 50)', validators=[Optional()])

    candidateTerm1 = StringField('Candidate Handle (Optional)')
    candidateTerm2 = StringField('Candidate Handle (Optional)')
    candidateTerm3 = StringField('Candidate Handle (Optional)')
    candidateTerm4 = StringField('Candidate Handle (Optional)')
    candidateTerm5 = StringField('Candidate Handle (Optional)')

    candidateAlias1 = StringField('Candidate Alias')
    candidateAlias2 = StringField('Candidate Alias')
    candidateAlias3 = StringField('Candidate Alias')
    candidateAlias4 = StringField('Candidate Alias')
    candidateAlias5 = StringField('Candidate Alias')

    search = SubmitField('Search!')
    # Buttons for historical search
    CA_Super_Tues = SubmitField("Super Tuesday in California")
    CA_Local = SubmitField("House Race in California")
    TX_Local = SubmitField("House Race in Texas")
    March10 = SubmitField("March 10th Election")

# Make Flask object
app = flask.Flask('twitter_sentiment')
# Disable the cache, ensuring up-to-date visualizations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Secret key required for form submission
app.config['SECRET_KEY'] = '5b73e80c580fcb85c325e459883c7f58'
# Initializing global TweetData object variable (to be defined in index())
obj = ""
# The default route
# (handling data submitted in a form)
@app.route('/', methods=['GET', 'POST'])
def index():
    '''
    This is what happens when a search query is entered on the Flask server.
    If the search is validated, it will call our functions to pull data from 
    Twitter, store it in a Pandas dataframe, and produce analyses of the 
    information.
    If the search is not validated, nothing happens.
    '''
    global obj

    form = SearchForm()
    result = []
    result1 = []
    result2 = []
    result3 = []
    result4 = []

    if form.validate_on_submit():
        # If the user enters a search term, the app will go here and query data in real
        # time.
        if form.search.data:
            # Formatting the input from the FlaskForm object so that our search functions
            # are ready to call.
            if not form.cityTerm.data or not form.stateTerm.data or not form.radiusVal.data:
                loc = {}
            else:
                loc = {"city": form.cityTerm.data, "state": form.stateTerm.data,
                       "radius": form.radiusVal.data}

            candidates = {form.candidateTerm1.data: [form.candidateAlias1.data], 
                          form.candidateTerm2.data: [form.candidateAlias2.data],
                          form.candidateTerm3.data: [form.candidateAlias3.data],
                          form.candidateTerm4.data: [form.candidateAlias4.data],
                          form.candidateTerm5.data: [form.candidateAlias5.data]}
            
            candidates.pop("", None)
            if not candidates:
                tweets = search_tweets(form.searchTerm.data, loc, result_type="recent")
            else:
                tweets = search_tweets(form.searchTerm.data, loc, result_type="recent", 
                                   candidates=candidates)
        # If the user does not enter  a search term and simply wants historical data,
        # they can access 4 summaries from recent election events.
        elif form.CA_Super_Tues.data:
            tweets = csv_to_tweets.go("CA_Super_Tuesday")
        elif form.CA_Local.data:
            tweets = csv_to_tweets.go("Local_Candidates/CA_local")
        elif form.March10:
            tweets = csv_to_tweets.go("Mar10_Elections")
        
        obj = tweets
        result = tweets.summarize_tweets_ab_candidates().split('\n')
        result1 = (['\n'] + tweets.summarize_follow_data().split('\n'))
        result2 = (['\n'] + tweets.summarize_sentiment("Follows ").split('\n'))
        result3 = (['\n'] + tweets.summarize_sentiment("Mentions ").split('\n'))
        result4 = (['\n'] + tweets.summarize_sentiment_by_followers_and_mentions().split('\n'))
        
    else:
        pass                                              

    return flask.render_template('main.html', title='Search page', form=form,
                                 result=result, result1=result1, result2=result2,
                                 result3=result3, result4=result4)


# route for a pie chart visualization
@app.route('/visual/', methods=['GET'])
def visual():
    '''
    Function to visualize tweet sentiment grouped by whether or not the tweet 
    mentions a particular candidate handle or alias.

    Makes use of the TweetData object created in index()
    '''
    img = BytesIO()
    
    labels = obj.data['Score_bins'].unique() 
    colors = ['orangered', 'coral', 'tan', 'yellowgreen', 'limegreen']
    mention_cols = [(col, col[9:]) for col in obj.data.columns if 'Mentions @' in col]

    fig, axs = plt.subplots(1, len(mention_cols), figsize=(15,4), constrained_layout=True)
    fig.suptitle('Tweets Mentioning:', fontsize=15)

    for i, (col, handle) in enumerate(mention_cols):
        filtered = obj.data[obj.data[col] == True]
        frac = (filtered.groupby('Score_bins').size()/len(filtered)).fillna(0)
        if (frac == 0).all():
            axs[i].text(-0.5, 0.70, 'Whoops! No tweets in your search \n mentioned {}!'.format(handle))
        axs[i].pie(frac, colors=colors, pctdistance=0.85, radius=1.25, startangle=90,\
                         autopct=lambda p: '{:.1f}%'.format(round(p)) if p > 0 else '')
        circle = plt.Circle((0,0),0.70,fc='white') 
        axs[i].add_artist(circle)
        axs[i].set_title('{} \n Number of tweets: {}'.format(handle, len(filtered)))
        axs[i].axis('equal')

    fig.legend(labels=labels, loc='lower center', ncol=5)
    fig.savefig(img, format='png')
    img.seek(0)

    return flask.send_file(img, mimetype='image/png')

# Route for a word cloud visualization
@app.route('/wordcloud/', methods=['GET'])
def wordcloud():
    '''
    Function to visualize a word cloud of the 250 most frequently occurring
    words in the tweet data pulled from the user request.

    Makes use of the TweetData object created in index()
    '''
    img = BytesIO()
    all_text = obj.data['TweetText'].sum().replace('\n', '')

    fig = plt.figure(figsize = (10,10))
    search_terms = obj.query.split()
    stopwords = set(STOPWORDS).union(set(search_terms))
    wordcloud = WordCloud(background_color='white',
                          stopwords=stopwords, 
                          max_words = 250, 
                          max_font_size = 30,
                          colormap='tab10').generate(all_text) 

    plt.imshow(wordcloud) 
    plt.title("Word Cloud for Your Search!", fontsize = 18) 
    plt.axis('off') 
    fig.savefig(img, format='png')
    img.seek(0)

    return flask.send_file(img, mimetype='image/png')
    

# Entry point for the app
if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True)
    