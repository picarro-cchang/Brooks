#include <stdio.h>
#include <stdlib.h>
#include "CuTest.h"
#include "cluster_analyzer.h"

typedef struct ca {
    double *xs;
    double d;
    int *weights;
    int npts;
    int *back;
    int *heap;
    int nh;
} CA;

static void init_weights(CA *self)
{
    int l, r;
    r = 0;
    for (l=0;l<self->npts;l++) {
        while (r<self->npts && self->xs[r]<=self->xs[l]+self->d) r++;
        self->weights[l] = r-l;
    }
}

static void init_ca(CA *self,double xs[],double d,int weights[],int npts)
{
    self->xs = xs;
    self->d = d;
    self->weights = weights;
    self->npts = npts;
    self->back = (int *) calloc(npts,sizeof(int));
    self->heap = (int *) calloc(npts,sizeof(int));
    self->nh = 0;
}

static void free_ca(CA *self)
{
    free(self->back);
    free(self->heap);
}

static int check_args(double xs[],double d,int weights[],unsigned int npts)
{
    unsigned int i;
    if (d<0) return ERROR_BADVALUE;
    for (i=1;i<npts;i++) {
        if (xs[i-1]>xs[i]) return ERROR_UNSORTED;
    }
    return SUCCESS;
}

static inline int value(CA *self,unsigned int n)
/* Get the weight of the heap entry n, or -1 if we are past the 
   end of the heap */
{
    if (n < self->nh) return self->weights[self->heap[n]];
    else return -1;
}

static inline void swap(CA *self,unsigned int n1,unsigned int n2)
/* Swap heap entries n1 and n2 */
{
    unsigned int temp = self->heap[n1];
    self->back[temp] = n2;
    self->back[self->heap[n2]] = n1;
    self->heap[n1] = self->heap[n2];
    self->heap[n2] = temp;
}

static void promote(CA *self,unsigned int n)
/* Promote the entry at heap position n */
{
    while (n>0) {
        unsigned int p = (n-1)>>1; // Parent of n
        if (value(self,n) > value(self,p)) {
            swap(self,n,p);
            n = p;
        }
        else break;
    }
}

static void insert_weights(CA *self)
/* Insert weights into the priority heap */
{
    unsigned int i;
    for (i=0; i<self->npts; i++) {
        self->back[i] = self->nh;
        self->heap[self->nh] = i;
        self->nh++;
        promote(self,self->nh-1);
    }
}

static void demote(CA *self,unsigned int n)
/* Demote the entry at heap position n */
{
    while (1) {
        unsigned int c1 = (n<<1) + 1; // Left child
        unsigned int c2 = (n+1) << 1; // Right child
        int v = value(self,n);
        int v1 = value(self,c1);
        int v2 = value(self,c2);
        if (v<v1 || v<v2) {
            // Promote the higher weighted child and slide down
            if (v1<v2) {
                swap(self,n,c2);
                n = c2;
            }
            else {
                swap(self,n,c1);
                n = c1;
            }
        }
        else break;
    }
}

static void change_weight(CA *self,unsigned int n,int new_weight)
/* Change weight of heap entry n and rearrange heap if necessary */
{
    self->weights[self->heap[n]] = new_weight;
    promote(self,n);
    demote(self,n);
}

static int pop(CA *self,unsigned int n)
/* Get heap entry n and rearrange heap */
{
    int result = value(self,n);
    self->nh--;
    swap(self,n,self->nh);
    promote(self,n);
    demote(self,n);
    return result;
}

int find_clusters(double *xs,double d,int *weights,unsigned int npts)
/* Find clusters of points of diameter not exceeding d from the npts
    specified in the array xs, which are in non-descending order */
{
    CA ca;
    int stat = check_args(xs,d,weights,npts);
    if (stat != SUCCESS) return stat;
    init_ca(&ca,xs,d,weights,npts);
    init_weights(&ca);
    insert_weights(&ca);
    printf("nh: %d\n", ca.nh);
    while (ca.nh > 0) {
        int start = ca.heap[0];
        int length = value(&ca,0);
        int k;
        double x = ca.xs[start];
        // printf("Removing cluster at %d of length %d\n",start,length);
        // Remove points in this group from the heap
        for (k=start;k<start+length;k++) {
            pop(&ca,ca.back[k]);
            ca.back[k] = -1;
        }
        // Change weights of points going backwards from start
        k = 1;
        while (start>=k && ca.xs[start-k]>=x-ca.d) {
            if (ca.back[start-k]>=0) change_weight(&ca,ca.back[start-k],k);
            k += 1;
        }
    }
    free_ca(&ca);
    return SUCCESS;
}

void dump_heap(CA *self)
{
    unsigned int n;
    for (n=0;n<self->nh;n++) {
        printf("Entry: %4d, Pointer: %4d, Weight: %4d\n",n,self->heap[n],value(self,n));
        if (self->back[self->heap[n]] != n)
            printf("Error at: %4d, Heap: %4d, back[heap]: %4d\n",n,self->heap[n],self->back[self->heap[n]]);
    }
}

static int check_heap(CA *self)
/* Verify that the value each node of the heap is no less than the values 
    of its children */
{
    unsigned int n;
    for (n=0;n<self->nh;n++) {
        unsigned int c1 = (n<<1) + 1; // Left child
        unsigned int c2 = (n+1) << 1; // Right child
        int v = value(self,n);
        int v1 = value(self,c1);
        int v2 = value(self,c2);
        if (v<v1 || v<v2) return ERROR_BAD_HEAP;
        if (c1>=self->nh || c2>=self->nh) break;
    }
    return SUCCESS;
}

void TestClusterAnalyzerInit(CuTest *tc) {
    double xs[] = {1.0,1.5,2.0,3.0,4.0,4.5,5.0};
    int weights[sizeof(xs)/sizeof(double)];
    CA ca;
    unsigned int i, j, npts = sizeof(xs)/sizeof(double);
    double d = 2.0;
    CuAssertIntEquals(tc,SUCCESS,check_args(xs,d,weights,npts));
    init_ca(&ca,xs,d,weights,npts);
    init_weights(&ca);
    CuAssertPtrEquals(tc,xs,ca.xs);
    CuAssertTrue(tc, ca.d == 2.0);
    CuAssertPtrEquals(tc,weights,ca.weights);
    CuAssertIntEquals(tc,npts,ca.npts);
    CuAssertIntEquals(tc,0,ca.nh);
    CuAssertPtrNotNull(tc,ca.back);
    CuAssertPtrNotNull(tc,ca.heap);
    for (i=0; i<npts; i++) {
        int w = 0;
        for(j=i; j<npts; j++) {
            if (ca.xs[j]-ca.xs[i]<=d) w++;
        }
        CuAssertIntEquals(tc,w,ca.weights[i]);
    }
    free_ca(&ca);
}

void TestHeap(CuTest *tc) {
    double xs[] = {1.0,1.5,2.0,2.3,3.0,4.0,4.5,5.0};
    int weights[sizeof(xs)/sizeof(double)] = {3,2,7,1,5,6,4,8};
    CA ca;
    unsigned int i, j, npts = sizeof(xs)/sizeof(double);
    double d = 2.0;
    CuAssertIntEquals(tc,SUCCESS,check_args(xs,d,weights,npts));
    init_ca(&ca,xs,d,weights,npts);
    init_weights(&ca);
    insert_weights(&ca);
    while (ca.nh>0) {
        CuAssertIntEquals(tc,SUCCESS,check_heap(&ca));
        printf("%d\n",pop(&ca,0));
    }
    free_ca(&ca);
}

CuSuite* ClusterAnalyzerSuite() {
    CuSuite* suite = CuSuiteNew();
    SUITE_ADD_TEST(suite, TestClusterAnalyzerInit);
    SUITE_ADD_TEST(suite, TestHeap);
    return suite;
}
