/* File: fastLombmodule.c
 * This file is auto-generated with f2py (version:2).
 * f2py is a Fortran to Python Interface Generator (FPIG), Second Edition,
 * written by Pearu Peterson <pearu@cens.ioc.ee>.
 * See http://cens.ioc.ee/projects/f2py2e/
 * Generation date: Mon Jun 17 14:52:47 2019
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
static PyObject *fastLomb_error;
static PyObject *fastLomb_module;

/*********************** See f2py2e/cfuncs.py: typedefs ***********************/
/*need_typedefs*/

/****************** See f2py2e/cfuncs.py: typedefs_generated ******************/
/*need_typedefs_generated*/

/********************** See f2py2e/cfuncs.py: cppmacros **********************/
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
    if (err==NULL) err = fastLomb_error;
    PyErr_SetString(err,errmess);
  }
  return 0;
}


/********************* See f2py2e/cfuncs.py: userincludes *********************/
/*need_userincludes*/

/********************* See f2py2e/capi_rules.py: usercode *********************/


/* See f2py2e/rules.py */
extern void fastLomb(double*,double*,int,double,double,double*,double*,int,int*,int*,double*,double*);
/*eof externroutines*/

/******************** See f2py2e/capi_rules.py: usercode1 ********************/


/******************* See f2py2e/cb_rules.py: buildcallback *******************/
/*need_callbacks*/

/*********************** See f2py2e/rules.py: buildapi ***********************/

/********************************** fastLomb **********************************/
static char doc_f2py_rout_fastLomb_fastLomb[] = "\
px,py,nout,jmax,prob,datavar = fastLomb(x,y,ofac,hifac)\n\nWrapper for ``fastLomb``.\
\n\nParameters\n----------\n"
"x : input rank-1 array('d') with bounds (n)\n"
"y : input rank-1 array('d') with bounds (n)\n"
"ofac : input float\n"
"hifac : input float\n"
"\nReturns\n-------\n"
"px : rank-1 array('d') with bounds (np)\n"
"py : rank-1 array('d') with bounds (np)\n"
"nout : int\n"
"jmax : int\n"
"prob : float\n"
"datavar : float";
/* extern void fastLomb(double*,double*,int,double,double,double*,double*,int,int*,int*,double*,double*); */
static PyObject *f2py_rout_fastLomb_fastLomb(const PyObject *capi_self,
                           PyObject *capi_args,
                           PyObject *capi_keywds,
                           void (*f2py_func)(double*,double*,int,double,double,double*,double*,int,int*,int*,double*,double*)) {
  PyObject * volatile capi_buildvalue = NULL;
  volatile int f2py_success = 1;
/*decl*/

  double *x = NULL;
  npy_intp x_Dims[1] = {-1};
  const int x_Rank = 1;
  PyArrayObject *capi_x_tmp = NULL;
  int capi_x_intent = 0;
  PyObject *x_capi = Py_None;
  double *y = NULL;
  npy_intp y_Dims[1] = {-1};
  const int y_Rank = 1;
  PyArrayObject *capi_y_tmp = NULL;
  int capi_y_intent = 0;
  PyObject *y_capi = Py_None;
  int n = 0;
  double ofac = 0;
  PyObject *ofac_capi = Py_None;
  double hifac = 0;
  PyObject *hifac_capi = Py_None;
  double *px = NULL;
  npy_intp px_Dims[1] = {-1};
  const int px_Rank = 1;
  PyArrayObject *capi_px_tmp = NULL;
  int capi_px_intent = 0;
  double *py = NULL;
  npy_intp py_Dims[1] = {-1};
  const int py_Rank = 1;
  PyArrayObject *capi_py_tmp = NULL;
  int capi_py_intent = 0;
  int np = 0;
  int nout = 0;
  int jmax = 0;
  double prob = 0;
  double datavar = 0;
  static char *capi_kwlist[] = {"x","y","ofac","hifac",NULL};

/*routdebugenter*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_clock();
#endif
  if (!PyArg_ParseTupleAndKeywords(capi_args,capi_keywds,\
    "OOOO:fastLomb.fastLomb",\
    capi_kwlist,&x_capi,&y_capi,&ofac_capi,&hifac_capi))
    return NULL;
/*frompyobj*/
  /* Processing variable datavar */
  /* Processing variable ofac */
    f2py_success = double_from_pyobj(&ofac,ofac_capi,"fastLomb.fastLomb() 3rd argument (ofac) can't be converted to double");
  if (f2py_success) {
  /* Processing variable jmax */
  /* Processing variable nout */
  /* Processing variable x */
  ;
  capi_x_intent |= F2PY_INTENT_IN|F2PY_INTENT_C;
  capi_x_tmp = array_from_pyobj(NPY_DOUBLE,x_Dims,x_Rank,capi_x_intent,x_capi);
  if (capi_x_tmp == NULL) {
    if (!PyErr_Occurred())
      PyErr_SetString(fastLomb_error,"failed in converting 1st argument `x' of fastLomb.fastLomb to C/Fortran array" );
  } else {
    x = (double *)(PyArray_DATA(capi_x_tmp));

  /* Processing variable hifac */
    f2py_success = double_from_pyobj(&hifac,hifac_capi,"fastLomb.fastLomb() 4th argument (hifac) can't be converted to double");
  if (f2py_success) {
  /* Processing variable prob */
  /* Processing variable n */
  n = len(x);
  /* Processing variable np */
  np = (int)(0.5*ofac*hifac*n);
  /* Processing variable y */
  y_Dims[0]=n;
  capi_y_intent |= F2PY_INTENT_IN|F2PY_INTENT_C;
  capi_y_tmp = array_from_pyobj(NPY_DOUBLE,y_Dims,y_Rank,capi_y_intent,y_capi);
  if (capi_y_tmp == NULL) {
    if (!PyErr_Occurred())
      PyErr_SetString(fastLomb_error,"failed in converting 2nd argument `y' of fastLomb.fastLomb to C/Fortran array" );
  } else {
    y = (double *)(PyArray_DATA(capi_y_tmp));

  /* Processing variable px */
  px_Dims[0]=np;
  capi_px_intent |= F2PY_INTENT_HIDE|F2PY_INTENT_OUT|F2PY_INTENT_C;
  capi_px_tmp = array_from_pyobj(NPY_DOUBLE,px_Dims,px_Rank,capi_px_intent,Py_None);
  if (capi_px_tmp == NULL) {
    if (!PyErr_Occurred())
      PyErr_SetString(fastLomb_error,"failed in converting hidden `px' of fastLomb.fastLomb to C/Fortran array" );
  } else {
    px = (double *)(PyArray_DATA(capi_px_tmp));

  /* Processing variable py */
  py_Dims[0]=np;
  capi_py_intent |= F2PY_INTENT_HIDE|F2PY_INTENT_OUT|F2PY_INTENT_C;
  capi_py_tmp = array_from_pyobj(NPY_DOUBLE,py_Dims,py_Rank,capi_py_intent,Py_None);
  if (capi_py_tmp == NULL) {
    if (!PyErr_Occurred())
      PyErr_SetString(fastLomb_error,"failed in converting hidden `py' of fastLomb.fastLomb to C/Fortran array" );
  } else {
    py = (double *)(PyArray_DATA(capi_py_tmp));

/*end of frompyobj*/
#ifdef F2PY_REPORT_ATEXIT
f2py_start_call_clock();
#endif
/*callfortranroutine*/
        (*f2py_func)(x,y,n,ofac,hifac,px,py,np,&nout,&jmax,&prob,&datavar);
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
    capi_buildvalue = Py_BuildValue("NNiidd",capi_px_tmp,capi_py_tmp,nout,jmax,prob,datavar);
/*closepyobjfrom*/
/*end of closepyobjfrom*/
    } /*if (f2py_success) after callfortranroutine*/
/*cleanupfrompyobj*/
  }  /*if (capi_py_tmp == NULL) ... else of py*/
  /* End of cleaning variable py */
  }  /*if (capi_px_tmp == NULL) ... else of px*/
  /* End of cleaning variable px */
  if((PyObject *)capi_y_tmp!=y_capi) {
    Py_XDECREF(capi_y_tmp); }
  }  /*if (capi_y_tmp == NULL) ... else of y*/
  /* End of cleaning variable y */
  /* End of cleaning variable np */
  /* End of cleaning variable n */
  /* End of cleaning variable prob */
  } /*if (f2py_success) of hifac*/
  /* End of cleaning variable hifac */
  if((PyObject *)capi_x_tmp!=x_capi) {
    Py_XDECREF(capi_x_tmp); }
  }  /*if (capi_x_tmp == NULL) ... else of x*/
  /* End of cleaning variable x */
  /* End of cleaning variable nout */
  /* End of cleaning variable jmax */
  } /*if (f2py_success) of ofac*/
  /* End of cleaning variable ofac */
  /* End of cleaning variable datavar */
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
/****************************** end of fastLomb ******************************/
/*eof body*/

/******************* See f2py2e/f90mod_rules.py: buildhooks *******************/
/*need_f90modhooks*/

/************** See f2py2e/rules.py: module_rules['modulebody'] **************/

/******************* See f2py2e/common_rules.py: buildhooks *******************/

/*need_commonhooks*/

/**************************** See f2py2e/rules.py ****************************/

static FortranDataDef f2py_routine_defs[] = {
  {"fastLomb",-1,{{-1}},0,(char *)fastLomb,(f2py_init_func)f2py_rout_fastLomb_fastLomb,doc_f2py_rout_fastLomb_fastLomb},

/*eof routine_defs*/
  {NULL}
};

static PyMethodDef f2py_module_methods[] = {

  {NULL,NULL}
};

#if PY_VERSION_HEX >= 0x03000000
static struct PyModuleDef moduledef = {
  PyModuleDef_HEAD_INIT,
  "fastLomb",
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
PyMODINIT_FUNC PyInit_fastLomb(void) {
#else
#define RETVAL
PyMODINIT_FUNC initfastLomb(void) {
#endif
  int i;
  PyObject *m,*d, *s;
#if PY_VERSION_HEX >= 0x03000000
  m = fastLomb_module = PyModule_Create(&moduledef);
#else
  m = fastLomb_module = Py_InitModule("fastLomb", f2py_module_methods);
#endif
  Py_TYPE(&PyFortran_Type) = &PyType_Type;
  import_array();
  if (PyErr_Occurred())
    {PyErr_SetString(PyExc_ImportError, "can't initialize module fastLomb (failed to import numpy)"); return RETVAL;}
  d = PyModule_GetDict(m);
  s = PyString_FromString("$Revision: $");
  PyDict_SetItemString(d, "__version__", s);
#if PY_VERSION_HEX >= 0x03000000
  s = PyUnicode_FromString(
#else
  s = PyString_FromString(
#endif
    "This module 'fastLomb' is auto-generated with f2py (version:2).\nFunctions:\n"
"  px,py,nout,jmax,prob,datavar = fastLomb(x,y,ofac,hifac)\n"
".");
  PyDict_SetItemString(d, "__doc__", s);
  fastLomb_error = PyErr_NewException ("fastLomb.error", NULL, NULL);
  Py_DECREF(s);
  for(i=0;f2py_routine_defs[i].name!=NULL;i++)
    PyDict_SetItemString(d, f2py_routine_defs[i].name,PyFortranObject_NewAsAttr(&f2py_routine_defs[i]));

/*eof initf2pywraphooks*/
/*eof initf90modhooks*/

/*eof initcommonhooks*/


#ifdef F2PY_REPORT_ATEXIT
  if (! PyErr_Occurred())
    on_exit(f2py_report_on_exit,(void*)"fastLomb");
#endif

  return RETVAL;
}
#ifdef __cplusplus
}
#endif
