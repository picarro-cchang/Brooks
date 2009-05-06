#include <stdio.h>

typedef struct {
    float num[9];
    float den[9];
    float state[8];
    int ptr;
} FilterEnvType;

#define MAX_ORDER (8)

#define STATUS_OK (0)
#define ERROR_BAD_FILTER_COEFF (-1)

int filter1(float x, float *y,FilterEnvType *env)
// Apply a linear filter to x to give y. Coefficients and state are
//   stored in env
{
    int i;
    double hnew = x, r = 0.0;
    if (env->den[0] == 0.0) {
        *y = 0.0;
        return ERROR_BAD_FILTER_COEFF;
    }
    for (i=1;i<=MAX_ORDER;i++) {
        env->ptr++;
        if (env->ptr >= MAX_ORDER) env->ptr=0;
        hnew -= env->state[env->ptr]*env->den[i];
        r += env->state[env->ptr]*env->num[i];
    }
    hnew /= env->den[0];
    env->state[env->ptr] = hnew;
    r += env->num[0]*hnew;
    env->ptr--;
    if (env->ptr < 0) env->ptr=MAX_ORDER-1;
    *y = r;
    return STATUS_OK;
}

int filter2(float x, float *y,FilterEnvType *env)
// Apply a linear filter to x to give y. Coefficients and state are
//   stored in env
{
    int i;
    float div = env->den[0];
    if (div == 0.0) {
        *y = 0.0;
        return ERROR_BAD_FILTER_COEFF;
    }
    *y = env->state[0] + (env->num[0]/div)*x;
    for (i=0;i<MAX_ORDER-1;i++) {
        env->state[i] = env->state[i+1] + (env->num[i+1]*x - env->den[i+1]*(*y))/div;
    }
    env->state[MAX_ORDER-1] = (env->num[MAX_ORDER]*x - env->den[MAX_ORDER]*(*y))/div;
    return STATUS_OK;
}

FilterEnvType env1 = {{ 2.0049999875482172e-005,
                      -3.9679998735664412e-005,
                       1.9634000636870041e-005,
                       0.0,0.0,0.0,0.0,0.0,0.0 },
                     { 1.0,
                      -3.5799999237060547,
                       4.7880997657775879,
                      -2.835360050201416,
                       0.62726402282714844,
                       0.0,0.0,0.0,0.0 },
                     {0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0},
                      0};

FilterEnvType env2 = {{ 2.0049999875482172e-005,
                      -3.9679998735664412e-005,
                       1.9634000636870041e-005,
                       0.0,0.0,0.0,0.0,0.0,0.0 },
                     { 1.0,
                      -3.5799999237060547,
                       4.7880997657775879,
                      -2.835360050201416,
                       0.62726402282714844,
                       0.0,0.0,0.0,0.0 },
                     {0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0},
                      0};

void main()
{
    float x = 10000.0, y1, y2;
    while (1)
    {
        filter1(x,&y1,&env1);
        filter2(x,&y2,&env2);
        printf("%20.5f%20.5f\n",y1,y2);
    }
}
