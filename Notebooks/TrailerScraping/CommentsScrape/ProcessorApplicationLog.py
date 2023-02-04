workers_logs = {}

founded = False
# begin_process = False
with open("application.log.bk", "r") as f:
    for line in f.readlines():
        # if not begin_process:
        # if "INFO:root:Worker Number 0 Started, Api_key AIzaSyABtrfufYJyDa7VAS-bTEocGw6X-ASn6vI" in line:
        #  if founded:
        #    begin_process = True

        #  founded = True

        # if not begin_process:
        #  continue

        if "Api_key" in line:
            worker_number = line.split("Worker Number")[1].split("Started,")[0].strip()
        elif "Worker Number" in line:
            worker_number = line.split("Worker Number")[1].split(",")[0].strip()
        else:
            continue

        if worker_number not in workers_logs.keys():
            workers_logs[worker_number] = []
        workers_logs[worker_number].append(line)

processed_movies = {}
for worker_number in workers_logs:
    for log in workers_logs[worker_number]:
        if "Processing" in log:
            uniqueID = log.split("Processing: Movie UniqueID")[1].split(",")[0].strip()
            traier_id = log.split("Trailer ID")[1].split("\n")[0].strip()
            if uniqueID not in processed_movies.keys():
                processed_movies[uniqueID] = {}
        if "From total comment count" in log:
            processed_movies[uniqueID][traier_id] = log

counter = 0
for processed_movie in processed_movies:
    # print("ID {}, Movie {}".format(processed_movie, processed_movies[processed_movie]))
    for result in processed_movies[processed_movie]:
        sub_total1, sub_total2 = processed_movies[processed_movie][result].split(
            "From total comment count, must delete total_posterior_comments_count: ")[1].split(
            " + total_posterior_reply_count: ")
        sub_total1 = int(sub_total1)
        sub_total2 = int(sub_total2.split(" \n")[0])
        processed_movies[processed_movie][result] = sub_total1 + sub_total2
        # break
    # break

    # print("Result {}".format(result))
    # counter += 1

print("Amount of movies processsed {}".format(len(processed_movies)))
print("Amount of results processsed {}".format(counter))

# print(processed_movies["0"]['0'])


# print(processed_movies["0"])
