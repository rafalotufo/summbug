import numpy as np
import time

def pageRank(G, s = .85, maxerr = .001):
    """
    Computes the pagerank for each of the n states.

    Used in webpage ranking and text summarization using unweighted
    or weighted transitions respectively.


    Args
    ----------
    G: matrix representing state transitions
       Gij can be a boolean or non negative real number representing the
       transition weight from state i to j.
       In terms of votes or links Gij is the number of votes/links from i to j,
       therefore increasing the pagerank of node j.

    Kwargs
    ----------
    s: probability of following a transition. 1-s probability of teleporting
       to another state. Defaults to 0.85

    maxerr: if the sum of pageranks between iterations is bellow this we will
            have converged. Defaults to 0.001
    """
    n = G.shape[0] ## number of nodes, since G is a square matrix

    # transform G into markov matrix M
    M = np.array(G, np.float)
    rsums = np.array(M.sum(1)) ## find sum of rows
    ci, ri = M.nonzero() ## (i,j) that are not zero
    for i in xrange(M.shape[1]):  ## divede rows by the row sum
        if rsums[i]:
            M[i,:] /= rsums[i] 
    
    # bool array of sink states
    sink = rsums==0

    start_time = time.time()
    # Compute pagerank r until we converge
    ro, r = np.zeros(n), np.ones(n) ## a vector of zeros and another of ones of size n
    while np.sum(np.abs(r-ro)) > maxerr and time.time() - start_time < 60:
        ro = r.copy()
        # calculate each pagerank at a time
        for i in xrange(0,n):
            # inlinks of state i
            Ii = np.array(M[:,i]) ## get each row
            # account for sink states
            Si = sink / float(n)
            # account for teleportation to state i
            Ti = np.ones(n) / float(n)

            r[i] = ro.dot( (Ii + Si)*s + Ti*(1-s) )

    # return normalized pagerank
    return r/sum(r)




if __name__=='__main__':
    # Example extracted from 'Introduction to Information Retrieval'
    G = np.array([[0,0,1,0,0,0,0],
                  [0,1,1,0,0,0,0],
                  [1,0,1,1,0,0,0],
                  [0,0,0,1,1,0,0],
                  [0,0,0,0,0,0,1],
                  [0,0,0,0,0,1,1],
                  [0,0,0,1,1,0,1]])

    # votes-eval and votes-topic and desc
    # G = np.array([[1,1,1,0,1,1],
    #               [0,2,2,0,0,2],
    #               [0,3,1,0,0,2],
    #               [0,1,1,0,0,1],
    #               [1,1,1,0,0,2],
    #               [0,3,3,0,1,1]])

    # # votes-eval and votes-topic
    G = np.array([[0,0,0,0,1,0],
                  [0,0,1,0,0,1],
                  [0,2,0,0,0,1],
                  [0,0,0,0,0,0],
                  [1,0,0,0,0,1],
                  [0,2,2,0,1,0]])

    # desc
    # G = np.array([[1,1,1,0,0,1],
    #               [0,2,1,0,0,1],
    #               [0,1,1,0,0,1],
    #               [0,1,1,0,0,1],
    #               [0,1,1,0,0,1],
    #               [0,1,1,0,0,1]])

    # # votes-topic
    # G = np.array([[0,0,0,0,1,0],
    #               [0,0,1,0,0,1],
    #               [0,1,0,0,0,1],
    #               [0,0,0,0,0,0],
    #               [1,0,0,0,0,1],
    #               [0,1,1,0,1,0]])

    # # votes-eval
    # G = np.array([[0,0,0,0,0,0],
    #               [0,0,0,0,0,0],
    #               [0,1,0,0,0,0],
    #               [0,0,0,0,0,0],
    #               [0,0,0,0,0,0],
    #               [0,1,1,0,0,0]])


    print ', '.join(str(round(p, 2)) for p in pageRank(G,s=.86))
