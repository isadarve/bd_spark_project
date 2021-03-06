from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql import functions as F
from pyspark.ml.feature import StringIndexer, OneHotEncoder
from pyspark.ml.feature import VectorAssembler
from tools import kmeans_info, correlation_matrix
from pyspark.ml.stat import Correlation
import pandas as pd

spark = SparkSession.builder.appName("bd_spark.com").master('local[4]').getOrCreate()

################ BEGIN LOADING, FILTERING AND COMBINING ################
# columns to drop
drop_cols0 = ('ArrTime','ActualElapsedTime','TaxiIn','AirTime','Diverted','CarrierDelay','WeatherDelay','NASDelay',
             'SecurityDelay','LateAircraftDelay')
drop_cols1 = ('Cancelled','CancellationCode','FlightNum','TailNum','TaxiOut','Year','CRSDepTime')
drop_cols2 = ('Distance','CRSElapsedTime')
# reading data from csv
df_raw = spark.read.option('inferSchema',True).option('header',True).csv('1987.csv')
# dropping forbidden variables
df= df_raw.drop(*drop_cols0)
# dropping variables that we consider they dont give any valuable info
df = df.drop(*drop_cols1)
# combining columns to get planned speed of the plane
df = df.withColumn('CRSPlanSpeed', expr('Distance / CRSElapsedTime'))
# dropping varaibles used to create new columns
df = df.drop(*drop_cols2)
df = df.withColumn('ArrDelay',F.col('ArrDelay').cast('integer'))\
    .withColumn('DepDelay',F.col('DepDelay').cast('integer'))\
    .withColumn('DepTime',F.col('DepTime').cast('integer'))
df = df.na.drop('any')
# map strings to numbers with string indexer
stringIndexer = StringIndexer(inputCols=['UniqueCarrier','Origin','Dest'], outputCols=['UniqueCarrierIndx','OriginIndx','DestIndx'])
model = stringIndexer.fit(df)
df = model.transform(df)
# perform onehotencoding
encoder = OneHotEncoder(dropLast=False, inputCols=['UniqueCarrierIndx','OriginIndx','DestIndx'], outputCols=['UniqueCarrierOHE','OriginOHE','DestOHE'])
model= encoder.fit(df)
df = model.transform(df)
# dropping encoded columns
df = df.drop(*['UniqueCarrier','Origin','Dest'])
df = df.drop(*['UniqueCarrierIndx','OriginIndx','DestIndx'])
# showing final schema
df.printSchema()
df.show()
################ END LOADING, FILTERING AND COMBINING ################

################ BEGIN VARIBABLE ANALYSIS ################

file = open('bd_project/analysis.txt', 'w')


# Trains a k-means model.
inputCols = ['DepTime','ArrDelay']
file.write('Clustering'+str(inputCols)+'\n')
for i in range(2,6):
    info = kmeans_info(i,df,inputCols)
    file.write(info)

inputCols=['CRSArrTime','ArrDelay']
file.write('Clustering'+str(inputCols)+'\n')
for i in range(2,6):
    info = kmeans_info(i,df,inputCols)
    file.write(info)


file.write('Correlation Matrix\n')
int_cols = ['Month','DayofMonth','DayOfWeek','DepTime','CRSArrTime','DepDelay','CRSPlanSpeed','ArrDelay']
info = correlation_matrix(df,int_cols)
file.write(info)