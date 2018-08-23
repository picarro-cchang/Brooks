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
      
      wt = a(6)*(a(5)-1.0)
      fact = 1.0 + 0.02*atan(a(3))
      do 10 i = 1,m
          xs = a(4) + (x(i)-a(4))*fact
          call speval1(sa_xa,sa_ya,sa_y2a,na,xs-a(0),sa)
          call speval1(sb_xa,sb_ya,sb_y2a,nb,xs-a(0),sb)
          y(i) = a(1) + a(2)*((1.0-wt)*sa + wt*sb)
   10 continue
      end      
c======================================================================
      SUBROUTINE HUMLIK ( N, X, Y, K )

*     To calculate the Faddeeva function with relative error less than 10^(-4).
c======================================================================
cf2py intent(out)  :: K
cf2py intent(hide) :: N

* Arguments
      INTEGER N                                                         ! IN   Number of points
      REAL    X(0:N-1)                                                  ! IN   Input x array
      REAL    Y                                                         ! IN   Input y value >=0.0
      REAL    K(0:N-1)                                                  ! OUT  Real (Voigt) array

* Constants
      REAL        RRTPI                                                 ! 1/SQRT(pi)
      PARAMETER ( RRTPI = 0.56418958 )
      REAL        Y0,       Y0PY0,         Y0Q                          ! for CPF12 algorithm
      PARAMETER ( Y0 = 1.5, Y0PY0 = Y0+Y0, Y0Q = Y0*Y0  )
      REAL  C(0:5), S(0:5), T(0:5)
      SAVE  C,      S,      T
*     SAVE preserves values of C, S and T (static) arrays between procedure calls
      DATA C / 1.0117281,     -0.75197147,        0.012557727,
     &         0.010022008,   -0.00024206814,     0.00000050084806 /
      DATA S / 1.393237,       0.23115241,       -0.15535147,
     &         0.0062183662,   0.000091908299,   -0.00000062752596 /
      DATA T / 0.31424038,     0.94778839,        1.5976826,
     &         2.2795071,      3.0206370,         3.8897249 /

* Local variables
      INTEGER I, J                                                      ! Loop variables
      INTEGER RG1, RG2, RG3                                             ! y polynomial flags
      REAL ABX, XQ, YQ, YRRTPI                                          ! |x|, x^2, y^2, y/SQRT(pi)
      REAL XLIM0, XLIM1, XLIM2, XLIM3, XLIM4                            ! |x| on region boundaries
      REAL A0, D0, D2, E0, E2, E4, H0, H2, H4, H6                       ! W4 temporary variables
      REAL P0, P2, P4, P6, P8, Z0, Z2, Z4, Z6, Z8
      REAL XP(0:5), XM(0:5), YP(0:5), YM(0:5)                           ! CPF12 temporary values
      REAL MQ(0:5), PQ(0:5), MF(0:5), PF(0:5)
      REAL D, YF, YPY0, YPY0Q  

***** Start of executable code *****************************************

      YQ  = Y*Y                                                         ! y^2
      YRRTPI = Y*RRTPI                                                  ! y/SQRT(pi)

      IF ( Y .GE. 70.55 ) THEN                                          ! All points
        DO I = 0, N-1                                                   ! in Region 0
          XQ   = X(I)*X(I)
          K(I) = YRRTPI / (XQ + YQ)
        ENDDO
        RETURN
      ENDIF

      RG1 = 1                                                           ! Set flags
      RG2 = 1
      RG3 = 1

      XLIM0 = SQRT ( 15100.0 + Y*(40.0 - Y*3.6) )                       ! y<70.55
      IF ( Y .GE. 8.425 ) THEN
        XLIM1 = 0.0
      ELSE
        XLIM1 = SQRT ( 164.0 - Y*(4.3 + Y*1.8) )
      ENDIF
      XLIM2 = 6.8 - Y
      XLIM3 = 2.4*Y
      XLIM4 = 18.1*Y + 1.65
      IF ( Y .LE. 0.000001 ) THEN                                       ! When y<10^-6
       XLIM1 = XLIM0                                                    ! avoid W4 algorithm
       XLIM2 = XLIM0
      ENDIF
*.....
      DO I = 0, N-1                                                     ! Loop over all points
       ABX = ABS ( X(I) )                                               ! |x|
       XQ  = ABX*ABX                                                    ! x^2
       IF     ( ABX .GE. XLIM0 ) THEN                                   ! Region 0 algorithm
        K(I) = YRRTPI / (XQ + YQ)

       ELSEIF ( ABX .GE. XLIM1 ) THEN                                   ! Humlicek W4 Region 1
        IF ( RG1 .NE. 0 ) THEN                                          ! First point in Region 1
         RG1 = 0
         A0 = YQ + 0.5                                                  ! Region 1 y-dependents
         D0 = A0*A0
         D2 = YQ + YQ - 1.0
        ENDIF
        D = RRTPI / (D0 + XQ*(D2 + XQ))
        K(I) = D*Y   *(A0 + XQ)

       ELSEIF ( ABX .GT. XLIM2 ) THEN                                   ! Humlicek W4 Region 2 
        IF ( RG2 .NE. 0 ) THEN                                          ! First point in Region 2
         RG2 = 0
         H0 =  0.5625 + YQ*(4.5 + YQ*(10.5 + YQ*(6.0 + YQ)))            ! Region 2 y-dependents
         H2 = -4.5    + YQ*(9.0 + YQ*( 6.0 + YQ* 4.0))
         H4 = 10.5    - YQ*(6.0 - YQ*  6.0)
         H6 = -6.0    + YQ* 4.0
         E0 =  1.875  + YQ*(8.25 + YQ*(5.5 + YQ))
         E2 =  5.25   + YQ*(1.0  + YQ* 3.0)
         E4 =  0.75*H6
        ENDIF
        D = RRTPI / (H0 + XQ*(H2 + XQ*(H4 + XQ*(H6 + XQ))))
        K(I) = D*Y   *(E0 + XQ*(E2 + XQ*(E4 + XQ)))

       ELSEIF ( ABX .LT. XLIM3 ) THEN                                   ! Humlicek W4 Region 3
        IF ( RG3 .NE. 0 ) THEN                                          ! First point in Region 3
         RG3 = 0
         Z0 = 272.1014     + Y*(1280.829 + Y*(2802.870 + Y*(3764.966    ! Region 3 y-dependents
     &       + Y*(3447.629 + Y*(2256.981 + Y*(1074.409 + Y*(369.1989
     &       + Y*(88.26741 + Y*(13.39880 + Y)))))))))
         Z2 = 211.678      + Y*(902.3066 + Y*(1758.336 + Y*(2037.310
     &                     + Y*(1549.675 + Y*(793.4273 + Y*(266.2987
     &                     + Y*(53.59518 + Y*5.0)))))))
         Z4 = 78.86585     + Y*(308.1852 + Y*(497.3014 + Y*(479.2576
     &                     + Y*(269.2916 + Y*(80.39278 + Y*10.0)))))
         Z6 = 22.03523     + Y*(55.02933 + Y*(92.75679 + Y*(53.59518
     &                     + Y*10.0)))
         Z8 = 1.496460     + Y*(13.39880 + Y*5.0)
         P0 = 153.5168     + Y*(549.3954 + Y*(919.4955 + Y*(946.8970
     &       + Y*(662.8097 + Y*(328.2151 + Y*(115.3772 + Y*(27.93941
     &                     + Y*(4.264678 + Y*0.3183291))))))))
         P2 = -34.16955    + Y*(-1.322256+ Y*(124.5975 + Y*(189.7730
     &                     + Y*(139.4665 + Y*(56.81652 + Y*(12.79458
     &                     + Y*1.2733163))))))
         P4 = 2.584042     + Y*(10.46332 + Y*(24.01655 + Y*(29.81482
     &                     + Y*(12.79568 + Y*1.9099744))))
         P6 = -0.07272979  + Y*(0.9377051+ Y*(4.266322 + Y*1.273316))
         P8 = 0.0005480304 + Y*0.3183291
        ENDIF
        D = 1.7724538 / (Z0 + XQ*(Z2 + XQ*(Z4 + XQ*(Z6 + XQ*(Z8+XQ)))))
        K(I) = D*(P0 + XQ*(P2 + XQ*(P4 + XQ*(P6 + XQ*P8))))

       ELSE                                                             ! Humlicek CPF12 algorithm
        YPY0 = Y + Y0
        YPY0Q = YPY0*YPY0
        K(I) = 0.0
         DO J = 0, 5
          D = X(I) - T(J)
          MQ(J) = D*D
          MF(J) = 1.0 / (MQ(J) + YPY0Q)
          XM(J) = MF(J)*D
          YM(J) = MF(J)*YPY0
          D = X(I) + T(J)
          PQ(J) = D*D
          PF(J) = 1.0 / (PQ(J) + YPY0Q)
          XP(J) = PF(J)*D
          YP(J) = PF(J)*YPY0
         ENDDO

        IF ( ABX .LE. XLIM4 ) THEN                                      ! Humlicek CPF12 Region I
         DO J = 0, 5
          K(I) = K(I) + C(J)*(YM(J)+YP(J)) - S(J)*(XM(J)-XP(J))
         ENDDO

        ELSE                                                            ! Humlicek CPF12 Region II
         YF   = Y + Y0PY0
         DO J = 0, 5
          K(I) = K(I)
     &     + (C(J)*(MQ(J)*MF(J)-Y0*YM(J)) + S(J)*YF*XM(J)) / (MQ(J)+Y0Q)
     &     + (C(J)*(PQ(J)*PF(J)-Y0*YP(J)) - S(J)*YF*XP(J)) / (PQ(J)+Y0Q)
         ENDDO
         K(I) = Y*K(I) + EXP ( -XQ )
        ENDIF
       ENDIF
      ENDDO
*.....
      END
c======================================================================
      subroutine galatry( x, y, z, n, result, str, min_loss )
*     Evaluate the Galatry function
c======================================================================
cf2py intent(out)  :: result
cf2py intent(hide) :: n
      implicit none
      
      integer i, j, n, nmax, region
      real c3r, c4r, c5r, delta, nz, pi/3.1415926535897932384/
      real result(n), x(n), y, z
      real min_loss, str, v, xm
      complex c(0:8), f, sum, term, theta, q, w(0:8)
 
      xm = y*sqrt(abs(str/min_loss-1.0))
      xm = min(max(xm,10.0),300.0)
 
      y = abs(y)
      z = abs(z)
      
      if (z.lt.0.04 .and. y.lt.0.5) then
          region = 1
      else if (z.lt.0.1) then
          region = 3
      else if (z.gt.5.0) then
          region = 2
      else if (y.gt.4.0*z**0.868) then
          region = 3
      else
          region = 2
      endif

      if (region.eq.1) then
          c3r = z/12.0
          c4r = -z**2/48.0
          c5r = z**3/240.0
          c(0) = 1.0
          c(1) = 0.0
          c(2) = 0.0
          c(3) = cmplx(0.0,c3r)
          c(4) = c4r
          c(5) = cmplx(0.0,-c5r)
          c(6) = -1.0*(-z**4/1440.0 + c3r**2/2.0)
          c(7) = cmplx(0.0,z**5/10080.0 + c3r*c4r)
          c(8) = -z**6/80640.0 + c3r*c5r + c4r**2/2.0
          do 10 i = 1,n
              if (abs(x(i)).gt.xm) then
                  result(i) = 0.0
              else
                  call humlik(1,x(i),y,v)
                  q = cmplx(x(i),y)
                  w(0) = v
                  w(1) = -2.0*(q*w(0))+cmplx(0.0,2.0/sqrt(pi))
                  w(2) = -2.0*(w(0)   + q*w(1))
                  w(3) = -2.0*(2.0*w(1) + q*w(2))
                  w(4) = -2.0*(2.0*w(2) + q*w(3))
                  w(5) = -2.0*(2.0*w(3) + q*w(4))
                  w(6) = -2.0*(2.0*w(4) + q*w(5))
                  w(7) = -2.0*(2.0*w(5) + q*w(6))
                  w(8) = -2.0*(2.0*w(6) + q*w(7))
                  result(i) = real(w(0)*c(0)+w(1)*c(1)+w(2)*c(2)+
     *             w(3)*c(3)+w(4)*c(4)+w(5)*c(5)+w(6)*c(6)+
     *             w(7)*c(7)+w(8)*c(8))
              endif
   10     continue
      else if (region.eq.2) then
          nmax = int(4 + z**(-1.05)*(1.0+3.0*exp(-1.1*y)))+1
          if (abs(nmax).gt.5000) then
              nmax = 5000
          endif
          delta = 0.5/(z**2)
          do 20 i = 1,n
              if (abs(x(i)).gt.xm) then 
                  result(i) = 0.0
              else
                  theta = cmplx(y,-x(i))/z + delta
                  sum = 0.0
                  term = 1.0/(z*sqrt(pi)*delta)
                  do 15 j = 0,nmax-1
                      term = term*delta/(j + theta)
                      sum = sum + term
   15             continue
                  result(i) = real(sum)
              endif
   20     continue
      else if (region.eq.3) then
          if (z.eq.0.0 .or. y.eq.0.0) then
              nmax = 100
          else 
              if (z.lt.0.2) then
                  nz = 5.0*sqrt(1.0/abs(z))
              else
                  nz = 0.0
              endif
              if (y.lt.0.2) then
                  nmax = int(2.0 + Nz + 37.0/sqrt(abs(y))*
     *                        exp(-0.6*y))+1
              else
                  nmax = int(2.0 + 37.0*exp(-0.6*y)) + 1
              endif
              if (nmax.gt.100) then
                  nmax = 100
              endif
          endif
          do 30 i = 1,n
              if (abs(x(i)).gt.xm) then 
                  result(i) = 0.0
              else
                  q = cmplx(y,-x(i))
                  f = 0.0
                  do 25 j = nmax,1,-1
                      f = 0.5*j/(f+j*z+q)
   25             continue
                  result(i) = real(1.0/(sqrt(pi)*(q+f)))
              endif
   30     continue
      endif 
      end
