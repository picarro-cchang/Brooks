# Validates the configuration file for the soil flux analyzer and supplies defaults

CONFIG_SPEC = """
[Lasers]
    # The section name specifies which laser
    [[__many__]]
    slope_factor = float(min=0.0, max=0.5, default=0.5)
    time_between_steps = integer(min=1, default=500)
    upper_window = integer(min=0, max=65535, default=45000)
    lower_window = integer(min=0, max=65535, default=20000)
    binning_rd = integer(min=10, default=400)
    update_levels = boolean(default=True)
    update_waveform = boolean(default=True)
"""
