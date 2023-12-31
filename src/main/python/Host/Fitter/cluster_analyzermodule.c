/* File: cluster_analyzermodule.c
 * This file is auto-generated with f2py (version:2).
 * f2py is a Fortran to Python Interface Generator (FPIG), Second Edition,
 * written by Pearu Peterson <pearu@cens.ioc.ee>.
 * See http://cens.ioc.ee/projects/f2py2e/
 * Generation date: Mon Nov 28 16:21:20 2022
 * $Revision:$
 * $Date:$
 * Do not edit this file directly unless you know what you are doing!!!
 */

#ifdef __cplusplus
extern "C" {
#endif

/*********************** See f2py2e/cfuncs.py: includes ***********************/
#include "Python.h"
#include <stdarg.h>
#include "fortranobject.h"
#include <math.h>

/**************** See f2py2e/rules.py: mod_rules['modulebody'] ****************/
static PyObject *cluster_analyzer_error;
static PyObject *cluster_analyzer_module;

/*********************** See f2py2e/cfuncs.py: typedefs ***********************/
/*need_typedefs*/

/****************** See f2py2e/cfuncs.py: typedefs_generated ******************/
/*need_typedefs_generated*/

/********************** See f2py2e/cfuncs.py: cppmacros **********************/
#if defined(PREPEND_FORTRAN)
#if defined(NO_APPEND_FORTRAN)
#if defined(UPPERCASE_FORTRAN)
#define F_FUNC(f,F) _##F
#else
#define F_FUNC(f,F) _##f
#endif
#else
#if defined(UPPERCASE_FORTRAN)
#define F_FUNC(f,F) _##F##_
#else
#define F_FUNC(f,F) _##f##_
#endif
#endif
#else
#if defined(NO_APPEND_FORTRAN)
#if defined(UPPERCASE_FORTRAN)
#define F_FUNC(f,F) F
#else
#define F_FUNC(f,F) f
#endif
#else
#if defined(UPPERCASE_FORTRAN)
#define F_FUNC(f,F) F##_
#else
#define F_FUNC(f,F) f##_
#endif
#endif
#endif
#if defined(UNDERSCORE_G77)
#define F_FUNC_US(f,F) F_FUNC(f##_,F##_)
#else
#define F_FUNC_US(f,F) F_FUNC(f,F)
#endif

#define rank(var) var ## _Rank
#define shape(var,dim) var ## _Dims[dim]
#define old_rank(var) (PyArray_NDIM((PyArrayObject *)(capi_ ## var ## _tmp)))
#define old_shape(var,dim) PyArray_DIM(((PyArrayObject *)(capi_ ## var ## _tmp)),dim)
#define fshape(var,dim) shape(var,rank(var)-dim-1)
#define len(var) shape(var,0)
#define flen(var) fshape(var,0)
#define old_size(var) PyArray_SIZE((PyArrayObject *)(capi_ ## var ## _tmp))
/* #define index(i) capi_i ## i */
#define slen(var) capi_ ## var ## _len
#define size(var, ...) f2py_size((PyArrayObject *)(capi_ ## var ## _tmp), ## __VA_ARGS__, -1)

#ifdef DEBUGCFUNCS
#define CFUNCSMESS(mess) fprintf(stderr,"debug-capi:"mess);
#define CFUNCSMESSPY(mess,obj) CFUNCSMESS(mess) \
  PyObject_Print((PyObject *)obj,stderr,Py_PRINT_RAW);\
  fprintf(stderr,"\n");
#else
#define CFUNCSMESS(mess)
#define CFUNCSMESSPY(mess,obj)
#endif

#ifndef max
#define max(a,b) ((a > b) ? (a) : (b))
#endif
#ifndef min
#define min(a,b) ((a < b) ? (a) : (b))
#endif
#ifndef MAX
#define MAX(a,b) ((a > b) ? (a) : (b))
#endif
#ifndef MIN
#define MIN(a,b) ((a < b) ? (a) : (b))
#endif


/************************ See f2py2e/cfuncs.py: cfuncs ************************/
static int f2py_size(PyArrayObject* var, ...)
{
  npy_int sz = 0;
  npy_int dim;
  npy_int rank;
  va_list argp;
  va_start(argp, var);
  dim = va_arg(argp, npy_int);
  if (dim==-1)
    {
      sz = PyArray_SIZE(var);
    }
  else
    {
      rank = PyArray_NDIM(var);
      if (dim>=1 && dim<=rank)
        sz = PyArray_DIM(var, dim-1);
      else
        fprintf(stderr, "f2py_size: 2nd argument value=%d fails to satisfy 1<=value<=%d. Result will be 0.\n", dim, rank);
    }
  va_end(argp);
  return sz;
}

static int double_from_pyobj(double* v,PyObject *obj,const char *errmess) {
  PyObject* tmp = NULL;
  if (PyFloat_Check(obj)) {
#ifdef __sgi
    *v = PyFloat_AsDouble(obj);
#else
    *v = PyFloat_AS_DOUBLE(obj);
#endif
    return 1;
  }
  tmp = PyNumber_Float(obj);
  if (tmp) {
#ifdef __sgi
    *v = PyFloat_AsDouble(tmp);
#else
    *v = PyFloat_AS_DOUBLE(tmp);
#endif
    Py_DECREF(tmp);
    return 1;
  }
  if (PyComplex_Check(obj))
    tmp = PyObject_GetAttrString(obj,"real");
  else if (PyString_Check(obj) || PyUnicode_Check(obj))
    /*pass*/;
  else if (PySequence_Check(obj))
    tmp = PySequence_GetItem(obj,0);
  if (tmp) {
    PyErr_Clear();
    if (double_from_pyobj(v,tmp,errmess)) {Py_DECREF(tmp); return 1;}
    Py_DECREF(tmp);
  }
  {
    PyObject* err = PyErr_Occurred();
    if (err==NULL) err = cluster_analyzer_error;
    PyErr_SetString(err,errmess);
  }
  return 0;
}


/********************* See f2py2e/cfuncs.py: userincludes *********************/
/*need_userincludes*/

/********************* See f2py2e/capi_rules.py: usercode *********************/


/* See f2py2e/rules.py */
extern int find_clusters(double*,double,int*,int);
/*eof externroutines*/

/******************** See f2py2e/capi_rules.py: usercode1 ********************/


/******************* See f2py2e/cb_rules.py: buildcallback *******************/
/*need_callbacks*/

/*********************** See f2py2e/rules.py: buildapi ***********************/

/******************************* find_clusters *******************************/
static char doc_f2py_rout_cluster_analyzer_find_clusters[] = "\
find_clusters,weights = find_clusters(xs,d)\n\nWrapper for ``find_clusters``.\
\n\nParameters\n----------\n"
"xs : input rank-1 array('d') with bounds (npts)\n"
"d : input float\n"
"\nReturns\n-------\n"
"find_clusters : int\n"
"weights : rank-1 array('i') with bounds (npts)";
/* extern int find_clusters(double*,double,int*,int); */
static PyObject *f2py_rout_cluster_analyzer_find_clusters(const PyObject *capi_self,
                           PyObject *capi_args,
                           PyObject *capi_keywds,
                           int (*f2py_func)(double*,double,int*,int)) {
  PyObject * volatile capi_buildvalue = NULL;
  volatile int f2py_success = 1;
/*decl*/

  int find_clusters_return_value=0;
  double *xs = NULL;
  npy_intp xs_Dims[1] = {-1};
  const int xs_Rank = 1;
  PyArrayObject *capi_xs_tmp = NULL;
  int capi_xs_intent = 0;
  PyObject *xs_capi = Py_None;
  double d = 0;
  PyObject *d_capi = Py_None;
  int *weights = NULL;
  npy_intp weights_Dims[1] = {-1};
  const int weights_Rank = 1;
  PyArrayObject *capi_weights_tmp = NULL;
  int capi_weights_intent = 0;
  int npts = 0;
  static char *capi_kwlist[] = {"xs","d",NULL};

/*routdebugenter*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_clock();
#endif
  if (!PyArg_ParseTupleAndKeywords(capi_args,capi_keywds,\
    "OO:cluster_analyzer.find_clusters",\
    capi_kwlist,&xs_capi,&d_capi))
    return NULL;
/*frompyobj*/
  /* Processing variable d */
    f2py_success = double_from_pyobj(&d,d_capi,"cluster_analyzer.find_clusters() 2nd argument (d) can't be converted to double");
  if (f2py_success) {
  /* Processing variable xs */
  ;
  capi_xs_intent |= F2PY_INTENT_IN|F2PY_INTENT_C;
  capi_xs_tmp = array_from_pyobj(NPY_DOUBLE,xs_Dims,xs_Rank,capi_xs_intent,xs_capi);
  if (capi_xs_tmp == NULL) {
    if (!PyErr_Occurred())
      PyErr_SetString(cluster_analyzer_error,"failed in converting 1st argument `xs' of cluster_analyzer.find_clusters to C/Fortran array" );
  } else {
    xs = (double *)(PyArray_DATA(capi_xs_tmp));

  /* Processing variable npts */
  npts = len(xs);
  /* Processing variable weights */
  weights_Dims[0]=npts;
  capi_weights_intent |= F2PY_INTENT_HIDE|F2PY_INTENT_OUT|F2PY_INTENT_C;
  capi_weights_tmp = array_from_pyobj(NPY_INT,weights_Dims,weights_Rank,capi_weights_intent,Py_None);
  if (capi_weights_tmp == NULL) {
    if (!PyErr_Occurred())
      PyErr_SetString(cluster_analyzer_error,"failed in converting hidden `weights' of cluster_analyzer.find_clusters to C/Fortran array" );
  } else {
    weights = (int *)(PyArray_DATA(capi_weights_tmp));

/*end of frompyobj*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_call_clock();
#endif
/*callfortranroutine*/
  find_clusters_return_value = (*f2py_func)(xs,d,weights,npts);
if (PyErr_Occurred())
  f2py_success = 0;
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_call_clock();
#endif
/*end of callfortranroutine*/
    if (f2py_success) {
/*pyobjfrom*/
/*end of pyobjfrom*/
    CFUNCSMESS("Building return value.\n");
    capi_buildvalue = Py_BuildValue("iN",find_clusters_return_value,capi_weights_tmp);
/*closepyobjfrom*/
/*end of closepyobjfrom*/
    } /*if (f2py_success) after callfortranroutine*/
/*cleanupfrompyobj*/
  }  /*if (capi_weights_tmp == NULL) ... else of weights*/
  /* End of cleaning variable weights */
  /* End of cleaning variable npts */
  if((PyObject *)capi_xs_tmp!=xs_capi) {
    Py_XDECREF(capi_xs_tmp); }
  }  /*if (capi_xs_tmp == NULL) ... else of xs*/
  /* End of cleaning variable xs */
  } /*if (f2py_success) of d*/
  /* End of cleaning variable d */
/*end of cleanupfrompyobj*/
  if (capi_buildvalue == NULL) {
/*routdebugfailure*/
  } else {
/*routdebugleave*/
  }
  CFUNCSMESS("Freeing memory.\n");
/*freemem*/
#ifdef F2PY_REPORT_ATEXIT
f2py_stop_clock();
#endif
  return capi_buildvalue;
}
/**************************** end of find_clusters ****************************/
/*eof body*/

/******************* See f2py2e/f90mod_rules.py: buildhooks *******************/
/*need_f90modhooks*/

/************** See f2py2e/rules.py: module_rules['modulebody'] **************/

/******************* See f2py2e/common_rules.py: buildhooks *******************/

/*need_commonhooks*/

/**************************** See f2py2e/rules.py ****************************/

static FortranDataDef f2py_routine_defs[] = {
  {"find_clusters",-1,{{-1}},0,(char *)find_clusters,(f2py_init_func)f2py_rout_cluster_analyzer_find_clusters,doc_f2py_rout_cluster_analyzer_find_clusters},

/*eof routine_defs*/
  {NULL}
};

static PyMethodDef f2py_module_methods[] = {

  {NULL,NULL}
};

#if PY_VERSION_HEX >= 0x03000000
static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "cluster_analyzer",
  NULL,
  -1,
  f2py_module_methods,
  NULL,
  NULL,
  NULL,
  NULL
};
#endif

#if PY_VERSION_HEX >= 0x03000000
#define RETVAL m
PyMODINIT_FUNC PyInit_cluster_analyzer(void) {
#else
#define RETVAL
PyMODINIT_FUNC initcluster_analyzer(void) {
#endif
  int i;
  PyObject *m,*d, *s;
#if PY_VERSION_HEX >= 0x03000000
  m = cluster_analyzer_module = PyModule_Create(&moduledef);
#else
  m = cluster_analyzer_module = Py_InitModule("cluster_analyzer", f2py_module_methods);
#endif
  Py_TYPE(&PyFortran_Type) = &PyType_Type;
  import_array();
  if (PyErr_Occurred())
    {PyErr_SetString(PyExc_ImportError, "can't initialize module cluster_analyzer (failed to import numpy)"); return RETVAL;}
  d = PyModule_GetDict(m);
  s = PyString_FromString("$Revision: $");
  PyDict_SetItemString(d, "__version__", s);
#if PY_VERSION_HEX >= 0x03000000
  s = PyUnicode_FromString(
#else
  s = PyString_FromString(
#endif
    "This module 'cluster_analyzer' is auto-generated with f2py (version:2).\nFunctions:\n"
"  find_clusters,weights = find_clusters(xs,d)\n"
".");
  PyDict_SetItemString(d, "__doc__", s);
  cluster_analyzer_error = PyErr_NewException ("cluster_analyzer.error", NULL, NULL);
  Py_DECREF(s);
  for(i=0;f2py_routine_defs[i].name!=NULL;i++)
    PyDict_SetItemString(d, f2py_routine_defs[i].name,PyFortranObject_NewAsAttr(&f2py_routine_defs[i]));

/*eof initf2pywraphooks*/
/*eof initf90modhooks*/

/*eof initcommonhooks*/


#ifdef F2PY_REPORT_ATEXIT
  if (! PyErr_Occurred())
    on_exit(f2py_report_on_exit,(void*)"cluster_analyzer");
#endif

  return RETVAL;
}
#ifdef __cplusplus
}
#endif
