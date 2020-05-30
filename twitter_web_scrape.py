from twitterscraper import query_tweets
import datetime as dt
import pandas as pd

begin_date = dt.date.today() - dt.timedelta(days=1)
end_date = dt.date.today()
limit = 100
language = 'english'
tweet_contents = ['Covid', 'covid', 'Covid-19', 'Coronavirus']

#if __name__ == '__main__':
list_of_tweets = query_tweets(tweet_contents, begindate=begin_date, enddate=end_date, limit=limit, lang=language)


tweets_df = pd.DataFrame(t.__dict__ for t in list_of_tweets)
tweets_df = tweets_df.filter(['screen_name','username','timestamp','text','likes','retweets','replies'], axis=1)
tweets_df = tweets_df.rename(columns={'text':'Tweet', 'timestamp':'Date','username':'Username','screen_name':'Handle'})
tweets_df['Handle'] = ('@' + tweets_df['Handle']).astype(str)

tweets_df.drop_duplicates(subset=['Handle','Username','Date','Tweet'], keep=False, inplace=True)
tweets_df.sort_values(by=['Date'], ascending=False, inplace=True)

#print(tweets_df.head())
tweets_df.to_csv('data/covid_tweets.csv', index=False)

