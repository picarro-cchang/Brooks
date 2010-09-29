c======================================================================
      subroutine speval1(xa,ya,y2a,n,x,y)
c======================================================================
cf2py intent(out)  :: y
cf2py intent(hide) :: n
      implicit none
      integer inc, k, klo/0/, khi, n
      double precision a, b, h, x, y 
      double precision xa(n), ya(n), y2a(n)

c Try to bracket point between xa(klo) and xa(klo+1). klo is used to remember the last successful search position.

      if (klo.le.0 .or. klo.gt.n) then                                  ! Go straight to bisection if klo is not useful
          klo = 0
          khi = n + 1
          goto 3
      endif
      inc = 1
      if (x.ge.xa(klo)) then                                            ! Hunt upwards
    1     khi = klo + inc
          if (khi.gt.n) then
              khi = n + 1
          else if (x.ge.xa(khi)) then
              klo = khi
              inc = 2*inc
              goto 1
          endif
      else                                                              ! Hunt downwards
          khi = klo
    2     klo = khi - inc
          if (klo.lt.1) then
              klo = 0
          else if (x.lt.xa(klo)) then
              khi = klo
              inc = 2*inc
              goto 2
          endif
      endif
c Perform bisection
    3 if (khi - klo.gt.1) then
          k = (khi + klo)/2
          if (x.lt.xa(k)) then
              khi = k
          else
              klo = k
          endif
          goto 3
      endif
c Evaluate spline          
      if (klo.eq.0) then
          y = ya(1)
      else if (klo.eq.n) then
          y = ya(n)
      else
          h = xa(khi) - xa(klo)
          a = (xa(khi) - x)/h
          b = (x - xa(klo))/h
          y = a*ya(klo) + b*ya(khi) +
     *        ((a**3-a)*y2a(klo)+(b**3-b)*y2a(khi))*(h**2)/6.0d0
      end if
      end      

c======================================================================
      subroutine speval(xa,ya,y2a,n,x,y,m)
c======================================================================
cf2py intent(out)  :: y
cf2py intent(hide) :: n
cf2py intent(hide) :: m

c Evaluates the cubic spline at the m points x from the values ya and 
c  second derivatives y2a specified at the n knots xa. Result is 
c  returned in y.
      implicit none
      integer i, m, n
      double precision xa(n), ya(n), y2a(n)
      double precision x(m), y(m)

      do 10 i = 1, m
          call speval1(xa,ya,y2a,n,x(i),y(i))
   10 continue
      end   

c======================================================================
      subroutine bseval(sa_xa,sa_ya,sa_y2a,na,sb_xa,sb_ya,sb_y2a,nb,
     *                  a,x,y,m)
c======================================================================
cf2py intent(out)  :: y
cf2py intent(hide) :: na
cf2py intent(hide) :: nb
cf2py intent(hide) :: m

c Evaluates the bi-spline at the m points x. The coefficient vector is 
c  a and the two splines which are to be combined are specified by 
c  arrays sa_* of length na and sb_* of length nb. Result is 
c  returned in y.

      implicit none
      integer i, m, na, nb
      double precision sa_xa(na), sa_ya(na), sa_y2a(na)
      double precision sb_xa(nb), sb_ya(nb), sb_y2a(nb)
      double precision x(m), y(m)
      double precision a(0:6)
      double precision xs, sa, sb, wt, fact
      
      wt = a(6)*(a(5)-1.0d0)
      fact = 1.0d0 + 0.02d0*atan(a(3))
      do 10 i = 1,m
          xs = a(4) + (x(i)-a(4))*fact
          call speval1(sa_xa,sa_ya,sa_y2a,na,xs-a(0),sa)
          call speval1(sb_xa,sb_ya,sb_y2a,nb,xs-a(0),sb)
          y(i) = a(1) + a(2)*((1.0d0-wt)*sa + wt*sb)
   10 continue
      end      
c======================================================================
      SUBROUTINE VOIGT( N, X, Y, K )
c======================================================================
cf2py intent(out)  :: K
cf2py intent(hide) :: N
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y
      DOUBLE COMPLEX K(N)
c
      INTEGER I
      DOUBLE PRECISION U, V
      LOGICAL FLAG
c
      DO I = 1,N
          CALL WOFZ(X(I),Y,U,V,FLAG)
          K(I) = DCMPLX(U,V)
      END DO
      END
C
C      ALGORITHM 680, COLLECTED ALGORITHMS FROM ACM.
C      THIS WORK PUBLISHED IN TRANSACTIONS ON MATHEMATICAL SOFTWARE,
C      VOL. 16, NO. 1, PP. 47.
      SUBROUTINE WOFZ (XI, YI, U, V, FLAG)
C
C  GIVEN A COMPLEX NUMBER Z = (XI,YI), THIS SUBROUTINE COMPUTES
C  THE VALUE OF THE FADDEEVA-FUNCTION W(Z) = EXP(-Z**2)*ERFC(-I*Z),
C  WHERE ERFC IS THE COMPLEX COMPLEMENTARY ERROR-FUNCTION AND I
C  MEANS SQRT(-1).
C  THE ACCURACY OF THE ALGORITHM FOR Z IN THE 1ST AND 2ND QUADRANT
C  IS 14 SIGNIFICANT DIGITS; IN THE 3RD AND 4TH IT IS 13 SIGNIFICANT
C  DIGITS OUTSIDE A CIRCULAR REGION WITH RADIUS 0.126 AROUND A ZERO
C  OF THE FUNCTION.
C  ALL REAL VARIABLES IN THE PROGRAM ARE DOUBLE PRECISION.
C
C
C  THE CODE CONTAINS A FEW COMPILER-DEPENDENT PARAMETERS :
C     RMAXREAL = THE MAXIMUM VALUE OF RMAXREAL EQUALS THE ROOT OF
C                RMAX = THE LARGEST NUMBER WHICH CAN STILL BE
C                IMPLEMENTED ON THE COMPUTER IN DOUBLE PRECISION
C                FLOATING-POINT ARITHMETIC
C     RMAXEXP  = LN(RMAX) - LN(2)
C     RMAXGONI = THE LARGEST POSSIBLE ARGUMENT OF A DOUBLE PRECISION
C                GONIOMETRIC FUNCTION (DCOS, DSIN, ...)
C  THE REASON WHY THESE PARAMETERS ARE NEEDED AS THEY ARE DEFINED WILL
C  BE EXPLAINED IN THE CODE BY MEANS OF COMMENTS
C
C
C  PARAMETER LIST
C     XI     = REAL      PART OF Z
C     YI     = IMAGINARY PART OF Z
C     U      = REAL      PART OF W(Z)
C     V      = IMAGINARY PART OF W(Z)
C     FLAG   = AN ERROR FLAG INDICATING WHETHER OVERFLOW WILL
C              OCCUR OR NOT; TYPE LOGICAL;
C              THE VALUES OF THIS VARIABLE HAVE THE FOLLOWING
C              MEANING :
C              FLAG=.FALSE. : NO ERROR CONDITION
C              FLAG=.TRUE.  : OVERFLOW WILL OCCUR, THE ROUTINE
C                             BECOMES INACTIVE
C  XI, YI      ARE THE INPUT-PARAMETERS
C  U, V, FLAG  ARE THE OUTPUT-PARAMETERS
C
C  FURTHERMORE THE PARAMETER FACTOR EQUALS 2/SQRT(PI)
C
C  THE ROUTINE IS NOT UNDERFLOW-PROTECTED BUT ANY VARIABLE CAN BE
C  PUT TO 0 UPON UNDERFLOW;
C
C  REFERENCE - GPM POPPE, CMJ WIJERS; MORE EFFICIENT COMPUTATION OF
C  THE COMPLEX ERROR-FUNCTION, ACM TRANS. MATH. SOFTWARE.
C
*
*
*
*
      IMPLICIT DOUBLE PRECISION (A-H, O-Z)
*
      LOGICAL A, B, FLAG
      PARAMETER (FACTOR   = 1.12837916709551257388D0,
     *           RMAXREAL = 0.5D+154,
     *           RMAXEXP  = 708.503061461606D0,
     *           RMAXGONI = 3.53711887601422D+15)
*
      FLAG = .FALSE.
*
      XABS = DABS(XI)
      YABS = DABS(YI)
      X    = XABS/6.3
      Y    = YABS/4.4
*
C
C     THE FOLLOWING IF-STATEMENT PROTECTS
C     QRHO = (X**2 + Y**2) AGAINST OVERFLOW
C
      IF ((XABS.GT.RMAXREAL).OR.(YABS.GT.RMAXREAL)) GOTO 100
*
      QRHO = X**2 + Y**2
*
      XABSQ = XABS**2
      XQUAD = XABSQ - YABS**2
      YQUAD = 2*XABS*YABS
*
      A     = QRHO.LT.0.085264D0
*
      IF (A) THEN
C
C  IF (QRHO.LT.0.085264D0) THEN THE FADDEEVA-FUNCTION IS EVALUATED
C  USING A POWER-SERIES (ABRAMOWITZ/STEGUN, EQUATION (7.1.5), P.297)
C  N IS THE MINIMUM NUMBER OF TERMS NEEDED TO OBTAIN THE REQUIRED
C  ACCURACY
C
        QRHO  = (1-0.85*Y)*DSQRT(QRHO)
        N     = IDNINT(6 + 72*QRHO)
        J     = 2*N+1
        XSUM  = 1.0/J
        YSUM  = 0.0D0
        DO 10 I=N, 1, -1
          J    = J - 2
          XAUX = (XSUM*XQUAD - YSUM*YQUAD)/I
          YSUM = (XSUM*YQUAD + YSUM*XQUAD)/I
          XSUM = XAUX + 1.0/J
 10     CONTINUE
        U1   = -FACTOR*(XSUM*YABS + YSUM*XABS) + 1.0
        V1   =  FACTOR*(XSUM*XABS - YSUM*YABS)
        DAUX =  DEXP(-XQUAD)
        U2   =  DAUX*DCOS(YQUAD)
        V2   = -DAUX*DSIN(YQUAD)
*
        U    = U1*U2 - V1*V2
        V    = U1*V2 + V1*U2
*
      ELSE
C
C  IF (QRHO.GT.1.O) THEN W(Z) IS EVALUATED USING THE LAPLACE
C  CONTINUED FRACTION
C  NU IS THE MINIMUM NUMBER OF TERMS NEEDED TO OBTAIN THE REQUIRED
C  ACCURACY
C
C  IF ((QRHO.GT.0.085264D0).AND.(QRHO.LT.1.0)) THEN W(Z) IS EVALUATED
C  BY A TRUNCATED TAYLOR EXPANSION, WHERE THE LAPLACE CONTINUED FRACTION
C  IS USED TO CALCULATE THE DERIVATIVES OF W(Z)
C  KAPN IS THE MINIMUM NUMBER OF TERMS IN THE TAYLOR EXPANSION NEEDED
C  TO OBTAIN THE REQUIRED ACCURACY
C  NU IS THE MINIMUM NUMBER OF TERMS OF THE CONTINUED FRACTION NEEDED
C  TO CALCULATE THE DERIVATIVES WITH THE REQUIRED ACCURACY
C
*
        IF (QRHO.GT.1.0) THEN
          H    = 0.0D0
          KAPN = 0
          QRHO = DSQRT(QRHO)
          NU   = IDINT(3 + (1442/(26*QRHO+77)))
        ELSE
          QRHO = (1-Y)*DSQRT(1-QRHO)
          H    = 1.88*QRHO
          H2   = 2*H
          KAPN = IDNINT(7  + 34*QRHO)
          NU   = IDNINT(16 + 26*QRHO)
        ENDIF
*
        B = (H.GT.0.0)
*
        IF (B) QLAMBDA = H2**KAPN
*
        RX = 0.0
        RY = 0.0
        SX = 0.0
        SY = 0.0
*
        DO 11 N=NU, 0, -1
          NP1 = N + 1
          TX  = YABS + H + NP1*RX
          TY  = XABS - NP1*RY
          C   = 0.5/(TX**2 + TY**2)
          RX  = C*TX
          RY  = C*TY
          IF ((B).AND.(N.LE.KAPN)) THEN
            TX = QLAMBDA + SX
            SX = RX*TX - RY*SY
            SY = RY*TX + RX*SY
            QLAMBDA = QLAMBDA/H2
          ENDIF
 11     CONTINUE
*
        IF (H.EQ.0.0) THEN
          U = FACTOR*RX
          V = FACTOR*RY
        ELSE
          U = FACTOR*SX
          V = FACTOR*SY
        END IF
*
        IF (YABS.EQ.0.0) U = DEXP(-XABS**2)
*
      END IF
*
*
C
C  EVALUATION OF W(Z) IN THE OTHER QUADRANTS
C
*
      IF (YI.LT.0.0) THEN
*
        IF (A) THEN
          U2    = 2*U2
          V2    = 2*V2
        ELSE
          XQUAD =  -XQUAD
*
C
C         THE FOLLOWING IF-STATEMENT PROTECTS 2*EXP(-Z**2)
C         AGAINST OVERFLOW
C
          IF ((YQUAD.GT.RMAXGONI).OR.
     *        (XQUAD.GT.RMAXEXP)) GOTO 100
*
          W1 =  2*DEXP(XQUAD)
          U2  =  W1*DCOS(YQUAD)
          V2  = -W1*DSIN(YQUAD)
        END IF
*
        U = U2 - U
        V = V2 - V
        IF (XI.GT.0.0) V = -V
      ELSE
        IF (XI.LT.0.0) V = -V
      END IF
*
      RETURN
*
  100 FLAG = .TRUE.
      RETURN
*
      END
c======================================================================
      subroutine galatry( x, y, z, n, result, str, min_loss )
*     Evaluate the Galatry function
c======================================================================
cf2py intent(out)  :: result
cf2py intent(hide) :: n
      implicit none
      
      integer i, j, n, nmax, region
      real*8 c3r, c4r, c5r, delta, nz, pi/3.1415926535897932384d0/
      real*8 result(n), x(n), y, z
      real*8 min_loss, str, xm
      complex*16 c(0:8), f, sum, term, theta, q, v(1), w(0:8)
 
      xm = y*sqrt(abs(str/min_loss-1.0d0))
      xm = min(max(xm,10.0d0),300.0d0)
 
      y = abs(y)
      z = abs(z)
      
      if (z.lt.0.04d0 .and. y.lt.0.5d0) then
          region = 1
      else if (z.lt.0.1d0) then
          region = 3
      else if (z.gt.5.0d0) then
          region = 2
      else if (y.gt.4.0d0*z**0.868d0) then
          region = 3
      else
          region = 2
      endif

      if (region.eq.1) then
          c3r = z/12.0d0
          c4r = -z**2/48.0d0
          c5r = z**3/240.0d0
          c(0) = 1.0d0
          c(1) = 0.0d0
          c(2) = 0.0d0
          c(3) = dcmplx(0.0d0,c3r)
          c(4) = c4r
          c(5) = dcmplx(0.0d0,-c5r)
          c(6) = -1.0d0*(-z**4/1440.0d0 + c3r**2/2.0d0)
          c(7) = dcmplx(0.0d0,z**5/10080.0d0 + c3r*c4r)
          c(8) = -z**6/80640.0d0 + c3r*c5r + c4r**2/2.0d0
          do 10 i = 1,n
              if (abs(x(i)).gt.xm) then
                  result(i) = 0.0d0
              else
                  call voigt(1,x(i),y,v)
                  q = dcmplx(x(i),y)
                  w(0) = v(1)
                  w(1) = -2.0d0*(q*w(0))+dcmplx(0.0d0,2.0d0/sqrt(pi))
                  w(2) = -2.0d0*(w(0)   + q*w(1))
                  w(3) = -2.0d0*(2.0d0*w(1) + q*w(2))
                  w(4) = -2.0d0*(3.0d0*w(2) + q*w(3))
                  w(5) = -2.0d0*(4.0d0*w(3) + q*w(4))
                  w(6) = -2.0d0*(5.0d0*w(4) + q*w(5))
                  w(7) = -2.0d0*(6.0d0*w(5) + q*w(6))
                  w(8) = -2.0d0*(7.0d0*w(6) + q*w(7))
                  result(i) = dble(w(0)*c(0)+w(1)*c(1)+w(2)*c(2)+
     *             w(3)*c(3)+w(4)*c(4)+w(5)*c(5)+w(6)*c(6)+
     *             w(7)*c(7)+w(8)*c(8))
              endif
   10     continue
      else if (region.eq.2) then
          nmax = int(4 + z**(-1.05d0)*(1.0d0+3.0d0*exp(-1.1d0*y)))+1
          if (abs(nmax).gt.5000) then
              nmax = 5000
          endif
          delta = 0.5d0/(z**2)
          do 20 i = 1,n
              if (abs(x(i)).gt.xm) then 
                  result(i) = 0.0d0
              else
                  theta = dcmplx(y,-x(i))/z + delta
                  sum = 0.0d0
                  term = 1.0d0/(z*sqrt(pi)*delta)
                  do 15 j = 0,nmax-1
                      term = term*delta/(j + theta)
                      sum = sum + term
   15             continue
                  result(i) = dble(sum)
              endif
   20     continue
      else if (region.eq.3) then
          if (z.eq.0.0d0 .or. y.eq.0.0d0) then
              nmax = 100
          else 
              if (z.lt.0.2d0) then
                  nz = 5.0d0*sqrt(1.0d0/abs(z))
              else
                  nz = 0.0d0
              endif
              if (y.lt.0.2d0) then
                  nmax = int(2.0d0 + Nz + 37.0d0/sqrt(abs(y))*
     *                        exp(-0.6d0*y))+1
              else
                  nmax = int(2.0d0 + 37.0d0*exp(-0.6d0*y)) + 1
              endif
              if (nmax.gt.100) then
                  nmax = 100
              endif
          endif
          do 30 i = 1,n
              if (abs(x(i)).gt.xm) then 
                  result(i) = 0.0d0
              else
                  q = dcmplx(y,-x(i))
                  f = 0.0d0
                  do 25 j = nmax,1,-1
                      f = 0.5d0*j/(f+j*z+q)
   25             continue
                  result(i) = dble(1.0d0/(sqrt(pi)*(q+f)))
              endif
   30     continue
      endif 
      end
