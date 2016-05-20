import numpy as np
from scipy.optimize import curve_fit

class PeakDection(object):
    def __init__(self):
        self.concentration_threshold = 100.0 #ppm
        self.dynamic_threshold = self.concentration_threshold
        self.retention_time_tolerance = 7.5 #seconds... approximately 4x std of repeated measurements...
        self.peak_cnt = 0
        self.peak_flag = False
        self.save_peak_data_flag = False
        self.slope_calc_flag = False
        self.current_peak_isotope_value = None
        self.current_peak_max_concentration = None
        self.current_peak_retention_time = None
        self.current_peak_approx_FWHM = None
        self.current_peak_threshold_bounds = [None,None]
        self.current_peak_integration_bounds = [None,None]
        self.current_peak_data_ready = False
        self.peak_assignment = None

    def detection_algo(self,vars):
        delay_idx = 0
        conc_idx = 1
        range_for_average = -4
        last_data_point = -1

        left_idx = 0
        right_idx = 1

        ### This parameter affects peak area that is integrated
        scalar = 0.001 #0.005 #0.135

        conc = vars[conc_idx]
        delay = vars[delay_idx]
        conc_subset = vars[conc_idx][range_for_average:last_data_point]
        delay_subset = vars[delay_idx][range_for_average:last_data_point]
        
        ### only run the detection algo if enough points exist
        if len(conc) > abs(range_for_average):
            moving_average = np.average(conc_subset)
            ### detect start of peak based on concentration threshold
            if moving_average > self.dynamic_threshold \
                and not self.peak_flag and not self.slope_calc_flag:
                ### record delay when concentration crosses threshold...
                self.peak_flag = True
                self.peak_detected(delay)
            ### detect end of peak based on concentration threshold
            elif moving_average < self.dynamic_threshold \
                and self.peak_flag and not self.slope_calc_flag:
                ### record delay when concentration crosses dynamic threshold...
                self.slope_calc_flag = True
                self.no_peak_detected(delay)
                ### calculate and record peak max and the slope to search for...
                self.calculate_peak_parameters(conc,delay)
            ### find the correct integration boundaries using the search slope
            elif self.peak_flag and self.slope_calc_flag \
                and self.is_ready_for_integration(conc_subset,delay_subset,scalar) \
                and moving_average < self.dynamic_threshold:
                self.peak_flag = False
                self.slope_calc_flag = False
                self.current_peak_integration_bounds[right_idx] = len(delay)
                self.current_peak_integration_bounds[left_idx] = \
                    self.search_for_left_bound(conc,delay,scalar)
                self.current_peak_data_ready = True

            if self.peak_flag:
            ### scale concentration threshold for peak detection using
            ### peak concentration of last peak... if the left bound doesn't exist,
            ### then the dynamic_threshold is equal to the initial concentation_threshold
                scalar_value = 20.0 # used to scale the threshold using the peak conc... set by hand
                index_start = delay.index(self.current_peak_threshold_bounds[0])
                dynamic_value = float(max(conc[index_start:]))/scalar_value
                self.dynamic_threshold = max(dynamic_value,self.concentration_threshold)
    
    def reset_dynamic_threshold(self):
        self.dynamic_threshold = self.concentration_threshold
        
        
    def peak_detected(self,delay):
        idx = 0
        increment = 1

        self.populate_threshold_bounds(idx,delay)
        self.peak_cnt += increment

    def no_peak_detected(self,delay):
        idx = 1
        self.populate_threshold_bounds(idx,delay)
        

    def populate_threshold_bounds(self,idx,delay):
        trigger_data_point = -3
        self.current_peak_threshold_bounds[idx] = delay[trigger_data_point]

    def calculate_peak_parameters(self,conc,delay):
        conversion_from_sigma_to_FWHM = 2.355
        default_FWHM = 25.0 #seconds is a rough estimate of typical FWHM
        
        idx_i = delay.index(self.current_peak_threshold_bounds[0])
        idx_f = delay.index(self.current_peak_threshold_bounds[1])

        x_data = delay[idx_i:idx_f]
        y_data = conc[idx_i:idx_f]
        offset = self.concentration_threshold
        

        self.current_peak_max_concentration = max(y_data)
        self.current_peak_retention_time = x_data[y_data.index(self.current_peak_max_concentration)]
        abs_ln_fraction = abs(np.log(self.concentration_threshold/self.current_peak_max_concentration))
                
        ### This calculation takes the y value of the threshold and the x value at which point
        ### the concentration trace crosses this threshold, and calculated the FWHM of the 
        ### concentration peak using the fraction of the threshold to the peak maximum... this
        ### assumes that the baseline CO2 concentration is near zero.
       
        self.current_peak_approx_FWHM = \
                1.665*(self.current_peak_retention_time-self.current_peak_threshold_bounds[0])/np.sqrt(abs_ln_fraction)
        if self.current_peak_approx_FWHM == 0:
            self.current_peak_approx_FWHM = default_FWHM
            
    def calculate_isotope_value(self,vars):
        left_bound, right_bound = 0,1
        delay_idx = 0
        conc_idx = 1
        delta_idx = 2
        
        
        left_idx = int(self.current_peak_integration_bounds[left_bound])
        right_idx = int(self.current_peak_integration_bounds[right_bound])

        conc = vars[conc_idx][left_idx:right_idx]
        delta = vars[delta_idx][left_idx:right_idx]
        time = vars[delay_idx][left_idx:right_idx]

        
        buffer_dist = 3
        baseline_conc = np.mean(vars[conc_idx][left_idx:left_idx+buffer_dist])
        ### baseline subtraction using 3 points in the beginning of the peak detection...
        conc = [conc_i - baseline_conc for conc_i in conc]
        ### re-write the peak concentration after baseline correction...
        self.current_peak_max_concentration = max(conc)
        
        ### integration ala simpson's rule
        
        ### the delta values used in the integration 
        ### are smoothed by 2-point moving window...
        ### this is becuase, quickly changing concentrations
        ### result in artifically noisy delta values...
        ### analysis on this shows a decrease in noise of about 30%...
        
        limit_of_reliable_delta = 15000 #ppm
        start_integration = 5000 #ppm
        ### Normal peak integration method...
        if self.current_peak_max_concentration < limit_of_reliable_delta:
            i = 0
            integrated_delta = 0
            integrated_conc = 0
            while i < len(time)-2:
                try:
                    time_factor = (time[i+2]-time[i])/6.0
                    integrated_conc += time_factor*(conc[i]+4*conc[i+1]+conc[i+2])
                    d_delta = time_factor*(conc[i]*np.average(delta[i:i+3])+4*conc[i+1]*np.average(delta[i+1:i+4])+conc[i+2]*np.average(delta[i+2:i+5]))
                    if not np.isnan(d_delta):
                        integrated_delta += d_delta
                except: pass
                i += 3
            self.current_peak_isotope_value = integrated_delta / integrated_conc
        
        ### Using tail of peak for integration...
        else:
            i = 0
            integrated_delta = 0
            integrated_conc = 0
            while i < len(time)-2:
                ### only integration over the right (or tail) side of the peak
                if time[i] > self.current_peak_retention_time and conc[i] < start_integration:
                    try:
                        time_factor = (time[i+2]-time[i])/6.0
                        integrated_conc += time_factor*(conc[i]+4*conc[i+1]+conc[i+2])
                        d_delta = time_factor*(conc[i]*np.average(delta[i:i+3])+4*conc[i+1]*np.average(delta[i+1:i+4])+conc[i+2]*np.average(delta[i+2:i+5]))
                        if not np.isnan(d_delta):
                            integrated_delta += d_delta
                    except: pass
                i += 3
            self.current_peak_isotope_value = integrated_delta / integrated_conc

    def is_ready_for_integration(self,conc,delay,scalar):
        '''This method checks to see if the current_slope, assuming the
        peak shape is a gaussian, is such that X% or so of the peak will
        be included in the integration. To do that, the current_slope is
        normalized using the peak_height and an approximation of the FWHM.
        '''
        
        current_slope = self.change(conc)/self.change(delay)
        #change integration threshold for concentrations above adn below 1000 ppm
        if self.current_peak_max_concentration < 1000:
            scalar = scalar/5.0
        threshold = scalar*self.current_peak_max_concentration
        threshold = threshold/self.current_peak_approx_FWHM
        return current_slope > -threshold

    def search_for_left_bound(self,conc,delay,scalar):
        '''This method searches backward in time to find the correct
        starting point for integration using the same assumptions as does
        the 'is_ready_for_integration' method.
        '''
        initialized_slope_value = 1.0e6 # arbitrary large number
        slope_range = 4 # separation used for calculating slope
        search_variable = 0
        search_increment = 1
        test_slope = initialized_slope_value
        test_left_bound = None
        test_right_bound = None

        idx_i = 0 #index for left most current_peak_threshold_bounds
        if self.current_peak_approx_FWHM != None:
            try:
                threshold = scalar*self.current_peak_max_concentration
                threshold = threshold/self.current_peak_approx_FWHM
                while test_slope > threshold:
                    test_right_bound = delay.index(self.current_peak_threshold_bounds[idx_i]) \
                        - search_variable
                    test_left_bound = test_right_bound - slope_range
                    test_slope = self.change(conc[test_left_bound:test_right_bound]) \
                        / self.change(delay[test_left_bound:test_right_bound])
                    search_variable += search_increment
                return test_left_bound
            except IndexError:
                return 0
        else:
            return 0


    def change(self,data):
        first_point = 0
        last_point = -1
        return float(data[last_point]-data[first_point])

    def clear_current_peak_variables(self):
        self.peak_flag = False
        self.save_peak_data_flag = False
        self.slope_calc_flag = False
        self.current_peak_isotope_value = None
        self.current_peak_max_concentration = None
        self.current_peak_retention_time = None
        self.current_peak_approx_FWHM = None
        self.current_peak_threshold_bounds = [None,None]
        self.current_peak_integration_bounds = [None,None]
        self.current_peak_data_ready = False
        self.peak_assignment = None