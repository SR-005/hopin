import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sematicweight=0.6
sematicheight=0.2

#Haversine's Distance Function
def distance(latitude1,longitude1,latitude2,longitude2):
    earthradius=6371        #radius of the earth


    latitude1radius=math.radians(latitude1)
    longitude1radius=math.radians(longitude1)
    latitude2radius=math.radians(latitude2)
    longitude2radius=math.radians(longitude2)

    latitudediff=latitude2radius-latitude1radius
    longitudediff=longitude2radius-longitude1radius


    return 0