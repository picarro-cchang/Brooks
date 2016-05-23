"""
Purpose: calculate rise time and fall time of a gas pulse. This is used in HCl and HF projects, and it's requested by Jim Lee
"""

def my_interp(x_value, x_array, y_array):
    old_value = None
    for i, value in enumerate(x_array):
        if old_value is not None:
            if (x_value - old_value) * (x_value - value) <= 0:
                right_index = i
                left_value, right_value = old_value, value
                break
        old_value = value
    else:
        raise
    alpha = (left_value - x_value) / (right_value - left_value)
    return y_array[right_index - 1] + alpha * (y_array[right_index] - y_array[right_index - 1])

# get percentile from user
dlg = _wx_.TextEntryDialog(None, "Percentile for calculating response time", defaultValue="90")
dlg.ShowModal()
percent = float(dlg.GetValue()) / 100.0
dlg.Destroy()

ax = _Figure_.gca()
tMin, tMax = ax.get_xlim()
selection = (x >= tMin) & (x <= tMax)
x_sel = x[selection]
y_sel = y[selection]
maximum, peak_location = max((v, i) for i, v in enumerate(y_sel))
minimum_left = min(y_sel[:peak_location])
minimum_right = min(y_sel[peak_location:])
rise_start_value = minimum_left + (maximum - minimum_left) * (1 - percent)
rise_end_value = minimum_left + (maximum - minimum_left) * percent
fall_start_value = minimum_right + (maximum - minimum_right) * percent
fall_end_value = minimum_right + (maximum - minimum_right) * (1 - percent)
rise_start_time = my_interp(rise_start_value, y_sel[:peak_location], x_sel[:peak_location])
rise_end_time = my_interp(rise_end_value, y_sel[:peak_location], x_sel[:peak_location])
fall_start_time = my_interp(fall_start_value, y_sel[peak_location:], x_sel[peak_location:])
fall_end_time = my_interp(fall_end_value, y_sel[peak_location:], x_sel[peak_location:])
if _Figure_.displayMode == "Minute":
    rise_response_time = (rise_end_time - rise_start_time) * 60.0
    fall_response_time = (fall_end_time - fall_start_time) * 60.0
elif _Figure_.displayMode == "Hour":
    rise_response_time = (rise_end_time - rise_start_time) * 3600.0
    fall_response_time = (fall_end_time - fall_start_time) * 3600.0
else:
    rise_response_time = (rise_end_time - rise_start_time) * 86400.0
    fall_response_time = (fall_end_time - fall_start_time) * 86400.0
    
result = "Calculation results of %d-%d response time in seconds:\nRise time, fall time = " % (percent*100, (1-percent)*100)
dlg = _wx_.TextEntryDialog(None, result, defaultValue="%s, %s" % (rise_response_time, fall_response_time))
dlg.ShowModal()
dlg.Destroy()