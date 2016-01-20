.. _fitting:

***************
Fitting
***************

.. _linear_fit:

Linear fit
==================================

Fit to linear function :math:`y = c_1 x + c_0`

.. _quadratic_fit:

Quadratic fit
==================================

Fit to quadratic function :math:`y = c_2 x^2 + c_1 x + c_0`

.. _polynomial_fit:

Polynomial fit
==================================

Fit to polynomial function of degree n: :math:`y = \Sigma c_n x^n`

.. _curve_fit:

Curve fit
==================================

Use non-linear least squares to fit an arbitray function to data.

.. image:: _static/curve_fit.jpg

* Initial guess is very important to curve fit. Try to make close guess to some parameters.

* If fitted to polynomial function, better to use :ref:`polynomial_fit`.
