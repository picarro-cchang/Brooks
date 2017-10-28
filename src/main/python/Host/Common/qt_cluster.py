import numpy as np

def qt_cluster(data, r_cluster):
    # Apply a one-dimensional form of the QT clustering algorithm to the set of points
    #  in the array data, using a r_cluster as the cluster radius.
    #
    # At each step, the algorithm moves an interval of diameter 2*r_cluster and finds 
    #  a position at which it covers the largest number of points in the current data
    #  set. These points form the next cluster and are removed from the set. The 
    #  algorithm is repeated with the remaining data set until no points remain.
    # The algorithm returns a list of clusters, where each cluster is a list of indices 
    #  in the original data which indicate the points which belong to that cluster. The 
    #  cluster sizes are in non-decreasing order.

    # Consider a set of points $\{x_1\le x_2\le ... \le x_n\}$. We wish to find a cluster 
    #  of radius $r$ centered at $\xi$ such that the number of points in the set lying 
    #  in the interval $(\xi-r,\xi+r]$ is maximized.
    #
    # First we define the function $N(x)=\#\{x_i: x_i\le x\}$. Then we effectively 
    #  consider maximizing $N(\xi+r)-N(\xi-r)$.
    #
    # The function $N$ is piecewise constant with unit jump discontinuities at each 
    #  $x_i$. Thus the function $m(x)=N(x)-N(x-2r)$ has upward jump discontinuities at 
    #  points $\{x_i\}$ and downward discontinuities at $\{x_i+2r\}$.

    n = len(data)
    disc = np.ones_like(data)
    x = np.concatenate((data, data + 2 * r_cluster))
    # Discontinuities in the function m
    disc = np.concatenate((disc, -disc))
    # We now sort the points in x. The function m has discontinuities at these points
    px = np.argsort(x)
    # Go through the points in sorted order

    clusters = []
    remaining = n

    while remaining > 0:
        #  Calulate v, which is the value of m just to the right of x[p]. Since the entries in x 
        #  need not be unique, we do not consider the value of m until the value of x at the 
        #  point after this one (in sorted order) is strictly greater, or if the end of the array 
        #  has been reached
        v = 0
        vmax = 0
        imax = 0
        lpx = len(px)
        for i, p in enumerate(px):
            # x[p] is the i'th ranked element of the points x. disc[p] is the discontinuity there
            v += disc[p]
            if (v>vmax) and ((i==lpx-1) or (x[p]!=x[px[i+1]])):
                vmax=v
                imax=i

        # We now remove all entries in x[:n] lying between x[px[imax]]-2*r and x[px[imax]].
        # Also remove all entries in x[n:] lying between x[px[imax]] and x[px[imax]]+2*r

        # i.e., start from position imax in px and go forwards until we exceed x[px[imax]]+2*r,
        #  remove any entry which has disc<0
        # also start from position imax in px and go backwards until we get less than x[px[imax]]-2*r
        #  remove any entry which has disc>0
        # The indices which are removed in this process are from the cluster with the most points
        # A point is removed by setting the discontinuity associated with it to zero. This means that
        #  when $m$ is subsequently recomputed, that point does not enter into the calculation.

        xpk = x[px[imax]]
        i = imax
        while i < len(px) and x[px[i]] <= xpk + 2*r_cluster:
            if disc[px[i]] < 0:   
                disc[px[i]] = 0
            i += 1
        i = imax
        cluster = []
        while i >= 0 and x[px[i]] >= xpk - 2*r_cluster:
            if disc[px[i]] > 0:   
                cluster.append(px[i])
                disc[px[i]] = 0
            i -= 1
        clusters.append(cluster)
        remaining -= len(cluster)
    return clusters
    