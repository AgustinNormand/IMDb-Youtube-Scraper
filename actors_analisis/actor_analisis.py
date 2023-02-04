import pandas as pd
import ast

scraped_actors_14 = {}
data = pd.read_csv("14_dic/scraped_actors.csv")
for actor_name in data.columns:
    if actor_name in scraped_actors_14.keys():
        print("Actor was already in dict")

    scraped_actors_14[actor_name] = {}
    movies = data[actor_name][0]
    star_before = data[actor_name][1]
    specific_url = data[actor_name][2]
    scraped_actors_14[actor_name]["movies"] = ast.literal_eval(movies)
    scraped_actors_14[actor_name]["url"] = specific_url
    scraped_actors_14[actor_name]["star_before"] = ast.literal_eval(star_before)

scraped_actors_12 = {}
data = pd.read_csv("12_dic/scraped_actors.csv")
for actor_name in data.columns:
    if actor_name in scraped_actors_12.keys():
        print("Actor was already in dict")

    scraped_actors_12[actor_name] = {}
    movies = data[actor_name][0]
    star_before = data[actor_name][1]
    specific_url = data[actor_name][2]
    scraped_actors_12[actor_name]["movies"] = ast.literal_eval(movies)
    scraped_actors_12[actor_name]["url"] = specific_url
    scraped_actors_12[actor_name]["star_before"] = ast.literal_eval(star_before)

for key in scraped_actors_14:
    if key not in scraped_actors_12.keys():
        #print("Actor of 14 not in 12 {}".format(key))
        pass

counter = 0
for key in scraped_actors_14:
    if key in scraped_actors_12.keys():
        if len(scraped_actors_14[key]["star_before"]) < len(scraped_actors_12[key]["star_before"]):
            counter += 1
            #print("Actor with different star before {}".format(key))
            #print("star_before 14 {}".format(scraped_actors_14[key]["star_before"]))
            #print("star_before 12 {}".format(scraped_actors_12[key]["star_before"]))
#print(counter)

with open("14_dic/StarsScraper.log", "r") as f:
    lines = f.readlines()
    for line in lines:
        if "ERROR" in line:
            for word in line.split():
                if "https://" in word:
                    print("\"{}\",".format(word))
