import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from haversine import haversine, Unit

sematicweight=0.6
spacialweight=0.4

#Haversine's Distance Function- Price Calculation
def price(location1,location2):
    distance=haversine(location1, location2)    #calculating distance between two locations (in km)
    print(distance,"km")
    price=round(distance*1.3)       #1.3 rupees per km
    print("Price: ",price)
    return price
#price((10.1071868,76.3597351),(10.0463,76.3242))

#Haversine's Distance Function- Spacial Score Computation
def haversinefunction(location1,location2):
    distance=haversine(location1, location2)
    spatialscore=1/(1+distance)
    return spatialscore

def finalscore(riderroute,availabletrips):
    #creating an array with all route text- including riders input route(as first element)
    allroutes=[riderroute]
    for trip in availabletrips:
        allroutes.append(trip[0])
    print("Available Routes: ",allroutes)
    vectorizer=TfidfVectorizer()
    matrix=vectorizer.fit_transform(allroutes)

    similarity=cosine_similarity(matrix[0:1],matrix[1:])[0]
    print("After Cosine Similarity: ",similarity)

    spacialscore=haversine((10.1071868,76.3597351),(10.0463,76.3242))
    final=(sematicweight*similarity,spacialweight*spacialscore)

    for i,ride in enumerate(availabletrips):
        semanticscore=similarity[i]

        driverlocation=availabletrips[i][1]
        riderlocation=(10.1071868,76.3597351)
        spacialscore=haversinefunction(driverlocation,riderlocation)
        print("Spacial Score of ",i+1,": ",spacialscore)

        final=(sematicweight*semanticscore+spacialweight*spacialscore)
        print("Final Score of ",i+1,": ",final,"\n")



    return 0

finalscore("via pipeline",[["via main road",(10.1071868,76.3597351)],["via high court",(10.1265,76.3533)],  
                           ["via pipeline road",(10.1071868,76.3597351)],["via pipeline road",(10.0463,76.3242)]])  #aluva,pulinchode,aluva,hmt