
import ast
#the metropolitan opera hd live: puccini: la bohème official trailer

"""
id = 0
with open("ThirdSourceScraper.log", "r") as f:
    with  open("trailers.csv", "w") as f2:
        lines = f.readlines()
        for line in lines:
            print(line)
            if "https://" in line:
                url = line.split("DEBUG - ")[1].split(" ")[0]
            if "Results [" in line:
                results = ast.literal_eval(line.split("Results ")[1])
                f2.write(str(id)+",")
                f2.write(url+",")
                id += 1
                for result in results:
                    trailer_name = result[0].replace(",", "")
                    f2.write(trailer_name+",")
                    channel_name = result[1].replace(",", "")
                    f2.write(channel_name+",")
                f2.write("\n")

                if len(results) < 10:
                    print(url)
                    print(len(results))
                #first_split = line.split("requested")[1]
            #href, rest = first_split.split(",")
            #href = href.strip()
            #raiting = float(rest.split("raiting ")[1].replace("\n", ""))
            #f2.write("{},{}\n".format(href, raiting))

# TODO Agregar del nuevo log las peticiones de raiting 0
"""

channels = {}
id_trailers = {}
id = 0
with open("ThirdSourceScraper.log", "r") as f:
        lines = f.readlines()
        for line in lines:
            #print(line)
            if "https://" in line:
                url = line.split("DEBUG - ")[1].split(" ")[0]
            if "Results [" in line:
                id_trailers[id] = {}
                id_trailers[id]["url"] = url
                id_trailers[id]["trailers"] = []
                results = ast.literal_eval(line.split("Results ")[1])
                for result in results:
                    trailer_name = result[0].replace(",", "")
                    channel_name = result[1].replace(",", "")
                    id_trailers[id]["trailers"].append([trailer_name, channel_name])
                    if not channel_name in channels:
                        channels[channel_name] = 0
                    channels[channel_name] = channels[channel_name] + 1


                id += 1


print("{} different channels".format(len(channels.keys())))
#channels = {k: v for k, v in sorted(channels.items(), key=lambda item: item[1])}
#for channel in channels:
    #print("{} {}".format(channel, channels[channel]))



