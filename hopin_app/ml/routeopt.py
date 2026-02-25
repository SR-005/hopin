import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from haversine import haversine, Unit

sematicweight=0.6
sematicheight=0.2

#Haversine's Distance Function- Price Calculation
def price(location1,location2):
    distance=haversine(location1, location2)    #calculating distance between two locations (in km)
    print(distance,"km")
    price=round(distance*1.3)       #1.3 rupees per km
    print("Price: ",price)
    return price
price((10.1071868,76.3597351),(10.0463,76.3242))

#Haversine's Distance Function- Spacial Score Computation
def spacialscore(location1,location2):
    distance=haversine(location1, location2)
    spatialscore=1/(1+distance)
    return spatialscore

def finalscore(riderroute,riderlocation,availabletrips):
    #creating an array with all route text- including riders input route(as first element)
    allroutes=[riderroute]
    for trip in availabletrips:
        allroutes.append(trip)

    vectorizer=TfidfVectorizer()
    matrix=vectorizer.fit_transform(allroutes)
    return 0