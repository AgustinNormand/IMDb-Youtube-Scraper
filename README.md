# Jordan-Scrapper

Low level documentation available in Colab, the perpose of this file is high/mid level documentation.

## Box Office Mojo Scrapper

### Old API alternatives

### Fake Headers 

### Offset parameter

### <tr> in body

In the body of the html of Box Office Mojo:
![image](https://user-images.githubusercontent.com/48933518/203125818-14dfbbc7-f174-49d0-b1a3-0f6a9c4febaa.png)

The first <tr>, the one that has style="display none" wich means is hidden, contains info non relevant, non movies, its important to ignore it.
![image](https://user-images.githubusercontent.com/48933518/203126000-4611297e-257b-4aed-b326-1eb0cc76ce98.png)

The one that corresponds to the first movie, is instead, the second one <tr> in the <tbody>
![image](https://user-images.githubusercontent.com/48933518/203127371-6bdeb37d-94e5-4f90-8a60-1d4da7787596.png)

### Time wait between requests
