import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from haversine import haversine, Unit

sematicweight=0.6
sematicheight=0.2

#Haversine's Distance Function
def spacialscore(location1,location2):
    distance=haversine(location1, location2)
    spatialscore=1/(1+distance)
    return spatialscore

def finalscore(riderroute,riderlocation,availabletrips):
    allroutes=[riderroute]
    for trip in availabletrips:
        allroutes(trip)
    return 0