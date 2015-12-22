custom_params = ["background", "slope", "quad", "cubic"]

def custom_func(t, background, slope, quad, cubic):
    coeff = [cubic, quad, slope, background]
    return np.polyval(coeff, t)

def custom_guess(t, conc):
    slope0, background0 = np.polyfit(t, conc, 1)
    return background0, slope0, 0.0, 0.0
    