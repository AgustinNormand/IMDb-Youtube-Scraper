# IMDb-Youtube-Scraper

The perpose of this file is high/mid level documentation.

I started to do some first tests using Python, in Google Colab, because it is interactive, it has a good interaction between code, results and documentation. And also, a python program, although none of its modules is yet a final version, they are only prototypes.

## Box Office Mojo Scrapper

### Old API alternatives

I searched for existing libraries to do the task without reinventing the wheel.
The first result in google is https://github.com/lamlamngo/Box-Office-Mojo-API, an API whose last commit was in 2018, of only 11 commits.
It does not have current maintenance, it probably has things that no longer work.

In PyPi, there is a library available https://pypi.org/project/BoxOfficeMojo/ whose name and version is BoxOfficeMojo 0.0.9, the most recent version is from December 20, 2014, for the same reasons as the previous one, no I would use it.

Searching for more, without finding too much, I conclude that there are no libraries that facilitate the work of scraping this site, so I start to make my version of the scraper.

### Fake Headers 

I used the python fake_headers library to invent headers and trick the HTTP server, so as not to show that it is a script and thus avoid bans.

### Offset parameter

The next and previous buttons work by adding an offset to the query string.
![image](https://user-images.githubusercontent.com/48933518/203129568-2362ddde-3d26-4d72-8bd9-486fcff9698f.png)

When we click next, it increments it by 200 (since it starts at 0), so it will take 5 requests to get the initial 1000 results.
![image](https://user-images.githubusercontent.com/48933518/203129673-e4f1a567-937e-4df0-9f7e-1d2f24846d36.png)

### Duplicated names in movies
If we use the movie name from the "Release" column as it appears there, there are 8 duplicates, so the scraped amount is 992, specifically the duplicates are:

![image](https://user-images.githubusercontent.com/48933518/203147869-75815b32-9e52-4e4a-bfd7-ffa9ed277486.png)

One is Godzilla 2014
![image](https://user-images.githubusercontent.com/48933518/203148207-55ec41a0-ddc1-476d-8547-7b5ee47f0e3f.png)

The other one is Godzilla 1998
![image](https://user-images.githubusercontent.com/48933518/203148259-18f22c9a-eb8f-4fd6-8d32-ca8e71bd5c50.png)
  
Perhaps it would be convenient to add the year to the name of the movie, for example, because we are going to search for the trailers on YouTube using that name. Or when looking for the trailer, take this into consideration
  
### Time wait between requests

For each request that is made, it is necessary to add a small waiting time. Otherwise, the Box Office Mojo server detects too much traffic coming from a single device and blocks it.
