#!/usr/bin/python
def distance( s, t ): # argc and argv translated to python, I think
    f_len = len(s)+1 # I think we can have variables for these values and a separate list.
    s_len = len(t)+1 # so this gives us the length of each word
    d = [[0] * s_len for x in range(f_len)] # this took forever to figure out from C
    for i in range(f_len): # set the first row
        d[i][0] = i
        for j in range(s_len): # set the first column
            d[0][j]=j
    for i in range(1, f_len):
        for j in range(1, s_len):
            if s[i-1] == t[j-1]: # no change
                d[i][j] = d[i-1][j-1]
            else: # change, obviously
                d[i][j] = min( d[i-1][j], d[i][j-1], d[i-1][j-1] ) +1
    return d[f_len-1][s_len-1]  #this should work
