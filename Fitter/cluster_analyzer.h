#ifndef _CLUSTER_ANALYZER_H_
#define _CLUSTER_ANALYZER_H_

#define SUCCESS (0)
#define ERROR_BADVALUE (-1)
#define ERROR_UNSORTED (-2)
#define ERROR_BAD_HEAP (-3)

int find_clusters(double *xs,double d,int *weights,unsigned int npts);

#endif /* _CLUSTER_ANALYZER_H_ */
