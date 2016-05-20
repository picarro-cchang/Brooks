def erfcx(z):
    """This is an approximation to the scaled complementary error function"""
    sigma = 2
    N = 23
    tau = 12
    s = np.exp(sigma**2)/(tau*(sigma+z))
    for n0 in range(N):
        n = n0 + 1
        fac = np.exp(sigma**2 - (n*np.pi/tau)**2)
        A = 2*tau*fac*np.cos(2*n*np.pi*sigma/tau)
        B = 2*n*np.pi*fac*np.sin(2*n*np.pi*sigma/tau)
        s += (A*(sigma+z) + B)/((n*np.pi)**2 + (tau*(sigma+z))**2)
    return s

custom_params = ["background", "slope", "tau"]

def custom_func(t, background, slope, tau):
    tau_lim = max(1.0, tau)
    return background + slope * tau_lim*(2.0*np.sqrt(t/tau_lim)/np.sqrt(np.pi) + erfcx(np.sqrt(t/tau_lim)) - 1.0)

def custom_guess(t, conc):
    slope0, background0 = np.polyfit(t, conc, 1)
    tau0 = t.max() - t.min()
    return background0, slope0, tau0
    