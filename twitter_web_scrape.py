from twitterscraper import query_tweets
import datetime as dt
import pandas as pd

begin_date = dt.date.today() - dt.timedelta(days=1)
end_date = dt.date.today()
limit = 100
language = 'english'
tweet_contents_covid = ['Covid','Covid-19','covid19','Coronavirus']
tweet_contents_2 = ['quarantine','socialdistancing']


#if __name__ == '__main__':
list_of_tweets = query_tweets(tweet_contents_covid, begindate=begin_date, enddate=end_date, limit=limit, lang=language)
list_of_tweets2 = query_tweets(tweet_contents_2, begindate=begin_date, enddate=end_date, limit=limit, lang=language)

# merge dataframes together
tweets_df1 = pd.DataFrame(t.__dict__ for t in list_of_tweets)
tweets_df2 = pd.DataFrame(t.__dict__ for t in list_of_tweets2)
tweets_df = pd.concat([tweets_df1, tweets_df2], axis=0)

# clean up tweets
tweets_df = tweets_df.filter(['screen_name','username','timestamp','text','likes','retweets','replies'], axis=1)
tweets_df = tweets_df.rename(columns={'text':'Tweet', 'timestamp':'Date','username':'Username','screen_name':'Handle'})
tweets_df['Handle'] = ('@' + tweets_df['Handle']).astype(str)
tweets_df['Tweet'] = tweets_df['Tweet'].astype(str)

tweets_df = tweets_df.dropna()
tweets_df.drop_duplicates(subset=['Handle','Username','Date','Tweet'], keep=False, inplace=True)
tweets_df.sort_values(by=['Date'], ascending=False, inplace=True)

#print(tweets_df.head())
tweets_df.to_csv('data/covid_tweets.csv', index=False)

