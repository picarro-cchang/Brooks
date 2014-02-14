/* P3TXT.js */
//define ({
P3TXT = {
// lables and phrases
    working: "... working ..."
    , loading: "... Loading ..."
    , get_analyzer_list: "Get Surveyor List"
    , name_legend: "Name"
    , close: "Close"
    , save: "Save"
    , add: "Add"
    , add_user: "Add User"
    , add_system: "Add System"
    , view_edit: 'View/Edit'
    , view_metadata: 'View Metadata'
    , view_details: 'View Details'
    , get_log_list: "Get Log List"
    , download_csv: "Download CSV"
    , download_log: "Download txt"
    , submit_finder: "Submit PeakFinder Job"
    , submit_analyzer: "Submit PeakAnalyzer Job"
    , submit_meta_refresh: "Metadata Refresh" //"Submit MetaData refresh Job"
    , issue_password: "Issue new password"
    , issue_identity: "Issue new identity"
    , refresh_list: "Refresh List"
    , refresh_user_list: "Refresh User List"
    , refresh_psys_list: "Refresh Systems List"
    , show_user_list: "Show User List"
    , show_psys_list: "Show Systems List"
    , site_not_available: "$ site not available."
    , no_logs_found_for_type: "No logs found for logtype: $"
    , no_logs_found_for_analyzer: "No logs found for surveyor: $"
    , try_again: "Please try operation again."
    , if_error_contact_admin: "If issue continues, please contact Site Administration."
    , process_handle: "Process Handle: "
    , paren_users: "(Users)"
    , paren_systems: "(Systems)"
    , users: "Users"
    , systems: "Systems"
    , user: "User"
    , addAnzCred: "Add Surveyor Credential"
    , modify_user: "Modify User"
    , modify_system: "Modify System"
    , sign_off: "Sign Off"
    , map: "Map"
    , live_map: "Live Map"
    , map_log: "Map Log"
    , add_new_user: "Add new user"
    , modify_user_profile: "Modify user profile"
    , time_zone: "Time zone"
    , change: "Change"
    , click_map_select_timezone: "Click on map to select time zone"
    , cancel: "Cancel"
    , save_changes: "Save changes"
    , click_to_select_anz: "Click here to  select Surveyor"
    , first: "First"
    , last: "Last"
    , process: "Process"
    , select_analyzer: "Select Surveyor"
    , live: "Live"
    , picarro_end_user_agreement: "Picarro End User Agreement"
    , session_has_expired: "For security purposes, this session has expired."
    , click_to_sign_in: "Click to sign in"
    , please_sign_in: 'Please Sign in.'
    , return_to_admin_utility: 'Return to Users List'
    , show_log_calendar: 'Show Calendar'
    , show_log_list: 'Show List'
    , refresh: 'Refresh'
    , prior_month: '&lt; Prev Month'
    , next_month: 'Next Month &gt;'
    , prior_year: '&lt;&lt; Prev Year'
    , next_year: 'Next Year &gt;&gt;'
    , first_log: 'First Log'
    , last_log: 'Last Log'
    , today: 'Today'
    , correct_highlighted_fields: 'Please correct the highlighted field(s).'
    , csrf_abort: 'CSRF verification failed. Request aborted.'
    , user_password_invalid: "The User/Password combination entered is not valid."
    , enter_valid_user_password: "Please enter a valid User/Password combination."
    , unauthorized_admin_abort: 'Unauthorized admin request. Request aborted.'
    , enter_value_for_fld: "Please enter a value for $."
    , fld_cannot_be_blank: "$ cannot be blank."
    , fld_must_equal_fld: "$ must equal $."
    , svc_for_user_save_success: "$ changes for $ successful."
    , last_active: "Last Active"
    , archive: "Archive"
    , none: "None" // to show when nothing has been selected or displayed!
    , session_will_expire: "This login session will expire in three minutes."

    , start: "Start" // example Start: 12:05PM
    , end: "End" // example End: 12:25PM
    , user_logs: "User logs" // count of User_logs example  User Logs: 5
    , durration: "Durration"  // example Durration: (3h 5m)

// gdu text    
    , amp: 'Amp' 
    , sigma: 'HalfWidth' 
    , lat: 'Lat' 
    , lon: 'Long' 
    , ch4: 'CH4' 
    , conc: 'Concentration' 
    , delta: 'Delta' 
    , uncertainty: 'Uncertainty' 
    , note: 'Annotation' 
    , ok: 'OK'
    , save_note: 'Save Annotation'
    , download_files: 'Download Files'
    , download_concs: 'Download Concentration' 
    , download_peaks: 'Download Peaks' 
    , download_analysis: 'Download Analysis' 
    , download_notes: 'Download Notes' 
    , anz_cntls: 'Surveyor Controls' 
    , restart_log: 'Restart Log' 
    , switch_to_cptr: 'Start Capture' 
    , start_survey: "Start Survey" 
    , stop_survey: "Stop Survey" 
    , complete_survey: "Complete Survey" 
    , cancl_ref: 'Cancel Reference' 
    , cancl_cptr: 'Cancel Capture' 
    , cancl_ana: 'Cancel Analysis' 
    , cancl_ana_time: 's left: Cancel' 
    , calibrate: 'Analyze Reference Gas' 
    , shutdown: 'Shutdown Surveyor' 
    , select_log: 'Select Log' 
    , switch_to_prime: 'Switch to Prime View' 
    , peak: 'Peak' 
    , analysis: 'Analysis' 
    , path: 'Route' 
    , note_list: 'Select Note to view' 
    , conn_warning_hdr: 'Connection Warning' 
    , conn_warning_txt: 'There is a problem with the network connection. Please verify connectivity.' 
    , survey_mode: 'Survey Mode' 
    , capture_mode: 'Capture Mode' 
    , analyzing_mode: 'Analyzing Peak' 
    , inactive_mode: 'Inactive Mode' 
    , cancelling_mode: 'Canceling...' 
    , priming_mode: 'Priming inlet' 
    , purging_mode: 'Purging inlet' 
    , injection_pending_mode: 'Injecting Gas' 
    , prime_conf_msg: 'Do you want to switch to Prime View Mode? \n\nWhen the browser is in Prime View Mode  you will have control of the Surveyor.' 
    , change_min_amp: 'Min Amplitude'  //'Minimum Amplitude' 
    , change_stab_class: 'Stability Class'  //'Minimum Amplitude' 
    , restart_datalog_msg: 'Close current data log and open a new one?' 
    , shutdown_anz_msg: 'Do you want to shut down the Surveyor? \n\nWhen the analyzer is shutdown it can take 30 to 45 minutes warm up.' 
    , stop_survey_msg: 'Are you sure you want to stop collecting data?' 
    , cancel_cap_msg: 'Cancel capture and return to survey mode?' 
    , cancel_ana_msg: 'Cancel analysis and return to survey mode?' 
    , cancel_ref_msg: 'Cancel reference gas processing?' 
    , start_ref_msg: 'Connect reference gas bottle and open valve. Press OK when ready.' 
    , show_controls: 'Show Controls' 
    , show_dnote: 'Show route annotations' 
    , show_pnote: 'Show peak annotations' 
    , show_anote: 'Show analysis annotations' 
    , click_show_cntls: 'Click to show controls' 
    , map_controls: 'Map Controls' 
    , dnote: 'Route annotation' 
    , anote: 'Analysis annotation' 
    , pnote: 'Peak annotation' 
    , show_notes: 'Show user annotations on map' 
    , abubble: 'Isotopic Analysis' 
    , pbubble: 'Peak Bubbles' 
    , wbubble: 'Wind Markers' 
    , swath: 'Field of View' 
    , show_markers: 'Show system markers on map' 
    , show_txt: 'Show' 
    , hide_txt: 'Hide' 
    , plat_outline: 'Plat Outline' 
    , hlite_plat: 'Highlight Current Plat' 
    , remove_plat_hlite: 'Remove Current Highlight' 
    , remove_all_plat_hlite: 'Remove All Highlights' 
    , select_active_plat: 'Set as Active Plat' 
    , remove_active_plat: 'Set as Inactive Plat' 
    , remove_plat: 'Remove plat' 
    , working: 'Working' 
    , plat: 'Plat' 
    , calibration_pulse_injected: 'Reference gas injected'
    , concentration_sparkline: 'Concentration Plot'
    , wind_direction: 'Wind direction'
    , collapse_side_pane: '<<'
    , expand_side_pane: '>>'

    , stream_title: 'Data Transfer Status Indicators' 
    , stream_ok: 'Data Transfer OK' 
    , stream_warning: 'Intermittent Data Transfer' 
    , stream_failed: 'Data Transfer Failed' 
    , gps_title: 'GPS Status Indicators' 
    , gps_ok: 'GPS OK' 
    , gps_warning: 'Unreliable GPS Signal' 
    , gps_failed: 'GPS Failed' 
    , gps_uninstalled: 'GPS Not Detectable' 
    , ws_title: 'Weather Station Status Indicators' 
    , ws_ok: 'Weather Station OK' 
    , ws_failed: 'Weather Station Failed' 
    , ws_uninstalled: 'Weather Station Not Detectable' 
    , analyzer_title: 'Current Surveyor Status' 
    , cavity_p: 'Cavity Pressure' 
    , cavity_t: 'Cavity Temperature' 
    , wb_t: 'Warm Box Temperature' 

    , stab_star: "*: Use reported weather data" 
    , stab_a: "A: Very Unstable" 
    , stab_b: "B: Unstable" 
    , stab_c: "C: Slightly Unstable" 
    , stab_d: "D: Neutral" 
    , stab_e: "E: Slightly Stable" 
    , stab_f: "F: Stable" 

    , export_as_txt: "Export data as txt file." 
    , export_as_csv: "Export data as csv file." 

    , copyClipboard: "Ctrl-C copies cursor position to clipboard" 

    , survey_time: "Survey time" 
    , day: "Day" 
    , night: "Night" 
    , sunlight: "Solar Radiation" 
    , strong_sunlight: "Strong" 
    , moderate_sunlight: "Moderate" 
    , overcast_sunlight: "Overcast" 
    , cloud: "Cloud Cover" 
    , less50_cloud: "&lt;50%" 
    , more50_cloud: "&gt;50%" 
    , wind: "Wind" 
    , calm_wind: "Calm" 
    , light_wind: "Light" 
    , strong_wind: "Strong" 
    , choose: "Please select an option" 
    , select_weather: "Weather Conditions"

    , prime_not_avail_msg: "Prime View is not currently available for the requested Surveyor. Switching to standard Live view."

    
// datatables text
// NOTE: _XXXX_ are datatable variable names DO NOT CHANGE the variable names!!!
    , dt_sSearch: "Search"
    , dt_sPrevious: "Previous"
    , dt_sNext: "Next"
    , dt_sInfo: "Showing _START_ to _END_ of _TOTAL_ entries"
    , db_sInfoFiltered: "(filtered from _MAX_ total entries)"

// calendar
    , sun: "Sun"
    , mon: "Mon"
    , tue: "Tue"
    , wed: "Wed"
    , thu: "Thu"
    , fri: "Fri"
    , sat: "Sat"
    , sunday: "Sunday"
    , monday: "Monday"
    , tuesday: "Tuesday"
    , wednesday: "Wednesday"
    , thursday: "Thursday"
    , friday: "Friday"
    , saturday: "Saturday"
    , abv_jan: "Jan"
    , abv_feb: "Feb"
    , abv_mar: "Mar"
    , abv_apr: "Apr"
    , abv_may: "May"
    , abv_jun: "Jun"
    , abv_jul: "Jul"
    , abv_aug: "Aug"
    , abv_sep: "Sep"
    , abv_oct: "Oct"
    , abv_nov: "Nov"
    , abv_dec: "Dec"
    , january: "January"
    , february: "February"
    , march: "March"
    , april: "April"
    , may: "May"
    , june: "June"
    , july: "July"
    , august: "August"
    , september: "September"
    , october: "October"
    , november: "November"
    , december: "December"
    , colon: ":"

// default values
    , default_TZ: "America/Los_Angeles"
    , default_CN: "US"

// Service Legends
    , index_service: "Home"
    , gdu_service: "Picarro Surveyor&#8482; for Natural Gas Leaks"
    , gdu_service_title: "Picarro Surveyor&#8482; <span style='color: #008000'>for Natural Gas Leaks</span>"
    , gdurpt_service: "Picarro Surveyor&#8482; Report Generation Portal"
    , gdurpt_service_title: "Picarro Surveyor&#8482; <span style='color: #008000'>Report Generation Portal</span>"
    , userprofile_service: "User Profile"
    , admin_service: "User Administration"

// Field Name Legends
    , ANALYZER_NAME_legend: "Surveyor Name Group"
    , PRIVATE_IP_legend: "Private IP"
    , LOGNAME_legend: "Logname"
    , ANALYZER_legend: "Surveyor"
    , durr_legend: "Durration"
    , durrstr_legend: "Durration (string)"
    , etmname_legend: "Epoch (from  logname)"
    , maxetm_legend: "Max Epoch Time"
    , minetm_legend: "Min Epoch Time"
    , name_legend: "Name"
    , uid_legend: "User ID"
    , userid_legend: "User ID"
    , fname_legend: "First Name"
    , lname_legend: "Last Name"
    , dname_legend: "Display Name"
    , active_legend: "Active"
    , rprocs_legend: "Authorized Resources"
    , svcauth_legend: "Authorized Services"
    , psys_legend: "System"
    , desc_legend: "Description"
    , geobox_legend: "Geo Box [swLng,swLat,neLng,neLat]"
    , passwd_legend: "Password"
    , cnfpass_legend: "Confirm Password"
    , allowgdu_legend: "Allow Picarro Surveyor&#8482; for Natural Gas Leaks"
    , allowgdup_legend: "Allow Picarro Surveyor&#8482; for Natural Gas Leaks (Prime View)"
    , allowgdurpt_legend: "Allow Picarro Surveyor&#8482; Report Generation Portal"
    , allowgdurptf_legend: "Add &quot;FORCE&quot; switch to Picarro Surveyor&#8482; Report Generation Portal"
    , allowuserprofile_legend: "Allow User Profile"
    , allowadmin_legend: "Allow Administration"
    , allowactive_legend: "Activate the userid"
    , date_legend: "Date"
    , minamp_legend: 'Min Amplitude'  //'Minimum Amplitude'
    , stabclass_legend: 'Stability Class'

// Placeholder text
    , ANALYZER_NAME_placeholder: "Surveyor Name Group"
    , PRIVATE_IP_placeholder: "nnn.nnn.nnn.nnn:nnnn"
    , LOGNAME_placeholder: "Logname"
    , ANALYZER_placeholder: "Surveyor"
    , durr_placeholder: "nnnn"
    , durrstr_placeholder: "(nh:nm)"
    , etmname_placeholder: "nnnnnnnnnn"
    , maxetm_placeholder: "nnnnnnnnnn"
    , minetm_placeholder: "nnnnnnnnnn"
    , name_placeholder: "Name"
    , fname_placeholder: "First Name"
    , lname_placeholder: "Last Name"
    , dname_placeholder: "Display Name"
    , active_placeholder: "True/False"
    , rprocs_placeholder: "Resource:Qry, Resourse2:Qry..."
    , svcauth_placeholder: "svc,svc2,..."
    , desc_placeholder: "Description"
    , psys_placeholder: "System Name"
    , userid_placeholder: "User ID"
    , uid_placeholder: "User ID"
    , passwd_placeholder: "Password"
    , cnfpass_placeholder: "Confirm Password"
    , allowgdu_placeholder: "X"
    , allowgdup_placeholder: "X"
    , allowgdurpt_placeholder: "X"
    , allowuserprofile_placeholder: "X"
    , allowadmin_placeholder: "X"
    , allowactive_placeholder: "X"
            
// MAIN Titles & Text
    , MAIN_title: "Picarro P-Cubed"
    , MAIN_right_title_home: "P-Cubed Right Pane"
    , MAIN_right_title_pane: "P-Cubed Left Pane"
}


// COMPOUND Definitions
P3TXT.weekdayNms = [ P3TXT.sun, P3TXT.mon, P3TXT.tue, P3TXT.wed, P3TXT.thu, P3TXT.fri, P3TXT.sat ];
P3TXT.weekdayNames = [ P3TXT.sunday, P3TXT.monday, P3TXT.tuesday, P3TXT.wednesday,
    P3TXT.thursday, P3TXT.friday, P3TXT.saturday ];
P3TXT.monthNms = [ P3TXT.abv_jan, P3TXT.abv_feb, P3TXT.abv_mar, P3TXT.abv_apr,
    P3TXT.abv_may, P3TXT.abv_jun, P3TXT.abv_jul, P3TXT.abv_aug,
    P3TXT.abv_sep, P3TXT.abv_oct, P3TXT.abv_nov, P3TXT.abv_dec ];
P3TXT.monthNames = [ P3TXT.january, P3TXT.february, P3TXT.march, P3TXT.april, P3TXT.may,
    P3TXT.june, P3TXT.july, P3TXT.august, P3TXT.september, P3TXT.october,
    P3TXT.november, P3TXT.december ];

// DASHBOARD strings
P3TXT.dashboard = {};
P3TXT.dashboard.heading_dashboard = "Dashboard";
P3TXT.dashboard.heading_job_preparation = "Job Preparation";
P3TXT.dashboard.heading_instructions = "Instructions";
P3TXT.dashboard.get_instructions = "Browse for an instructions file, drag a file onto here or reload from dashboard.";
P3TXT.dashboard.heading_actions = "Actions";
P3TXT.dashboard.make_report = "Make Report";
P3TXT.dashboard.save_instructions = "Save Instructions";
P3TXT.dashboard.fieldname_title = "Title";
P3TXT.dashboard.placeholder_title = "Title";
P3TXT.dashboard.fieldname_make_pdf = "Make PDF";
P3TXT.dashboard.fieldname_sw_corner = "SW Corner";
P3TXT.dashboard.fieldname_ne_corner = "NE Corner";
P3TXT.dashboard.placeholder_latlng = "Latitude, Longitude";
P3TXT.dashboard.fieldname_report_time_zone = "Report time zone";
P3TXT.dashboard.fieldname_peaks_min_amp = "Peaks Min Amp";
P3TXT.dashboard.fieldname_peaks_exclusion_radius = "Exclusion Radius";
P3TXT.dashboard.fieldname_rows = "Rows";
P3TXT.dashboard.fieldname_columns = "Columns";
P3TXT.dashboard.heading_runs = "Runs";
P3TXT.dashboard.heading_user_marker_files = "User Marker Files";
P3TXT.dashboard.heading_facilities_files = "Facilities Files";
P3TXT.dashboard.edit_template = "Edit Template";
P3TXT.dashboard.heading_summary_pages = "Summary Pages";
P3TXT.dashboard.heading_submap_pages = "Submap Pages";
P3TXT.dashboard.option_peaks_table = "Peaks Table";
P3TXT.dashboard.option_isotopic_table = "Isotopic Table";
P3TXT.dashboard.option_runs_table = "Runs Table";
P3TXT.dashboard.option_surveys_table = "Surveys Table";

P3TXT.dashboard.empty_report = "Empty report, check template";
P3TXT.dashboard.send_code = "Please send this code to Picarro: ";
P3TXT.dashboard.report_expired = "Report not found or expired. ";
P3TXT.dashboard.alert_while_converting_timezone = "Server error while converting timezone: ";
P3TXT.dashboard.alert_invalid_instructions_file = "Invalid instructions file: ";
P3TXT.dashboard.alert_multiple_files = "Cannot process more than one file";
P3TXT.dashboard.alert_while_submitting_instructions = "While submitting instructions: ";
P3TXT.dashboard.alert_duplicate_instructions = "This is a duplicate of a previously submitted report";
P3TXT.dashboard.alert_while_getting_key_file_data = "While getting key file data from: ";
P3TXT.dashboard.alert_empty_summary = "Empty report - Use Edit Template to define a non-empty summary report.";
P3TXT.dashboard.alert_ref_to_empty_submap = "Summary report refers to empty submap report - Edit Template to resolve grid reference.";
P3TXT.dashboard.alert_unreachable_submap = "Submap report is unreachable from summary - Edit Template to resolve grid reference.";
P3TXT.dashboard.alert_no_runs ="No runs have been specified - do you want to make the report?";

// Table Headings
P3TXT.dashboard.th_analyzer = "Analyzer";
P3TXT.dashboard.th_startEtm = "Start";
P3TXT.dashboard.th_endEtm = "End";
P3TXT.dashboard.th_peaks = "Peaks";
P3TXT.dashboard.th_wedges = "LISA";
P3TXT.dashboard.th_analyses = "Isotopic";
P3TXT.dashboard.th_fovs = "FOV";
P3TXT.dashboard.th_stabClass = "Stab Class";

P3TXT.dashboard.th_baseType = "Type";
P3TXT.dashboard.th_facilities = "Facilities";
P3TXT.dashboard.th_paths = "Paths";
P3TXT.dashboard.th_markers = "Markers";
P3TXT.dashboard.th_submapGrid = "Grid";

P3TXT.dashboard.th_csv_filename = "CSV Filename";
P3TXT.dashboard.th_csv_hashAndName = "Download";
P3TXT.dashboard.th_kml_filename = "KML Filename";
P3TXT.dashboard.th_offsets = "Offsets";
P3TXT.dashboard.th_linewidth = "Line Width";
P3TXT.dashboard.th_linecolor = "Line Color";
P3TXT.dashboard.th_xpath = "XPath";
P3TXT.dashboard.th_kml_hashAndName = "Download";

// Dialogs for editing parameters
P3TXT.dashboard.runs_dlg_add_new_run = "Add new run";
P3TXT.dashboard.runs_dlg_analyzer = "Analyzer";
P3TXT.dashboard.runs_ph_analyzer = "Name of analyzer";
P3TXT.dashboard.runs_dlg_start_time = "Start Time";
P3TXT.dashboard.runs_ph_time = "YYYY-MM-DD HH:MM";
P3TXT.dashboard.runs_dlg_end_time = "End Time";
P3TXT.dashboard.runs_dlg_peaks = "Peaks";
P3TXT.dashboard.runs_dlg_wedges = "LISAs";
P3TXT.dashboard.runs_dlg_analyses = "Isotopic";
P3TXT.dashboard.runs_dlg_swath = "Field of View";
P3TXT.dashboard.runs_dlg_stab_class = "Stability Class";
P3TXT.dashboard.runs_dlg_stab_class_star = "*: Use reported weather data";
P3TXT.dashboard.runs_dlg_stab_class_a = "A: Very Unstable";
P3TXT.dashboard.runs_dlg_stab_class_b = "B: Unstable";
P3TXT.dashboard.runs_dlg_stab_class_c = "C: Slightly Unstable";
P3TXT.dashboard.runs_dlg_stab_class_d = "D: Neutral";
P3TXT.dashboard.runs_dlg_stab_class_e = "E: Slightly Stable";
P3TXT.dashboard.runs_dlg_stab_class_f = "F: Stable";

P3TXT.dashboard.submap_dlg_add_new_figure = "Add new figure for each submap";
P3TXT.dashboard.summary_dlg_add_new_figure = "Add new figure for summary";
P3TXT.dashboard.fig_dlg_background = "Background Type";
P3TXT.dashboard.fig_dlg_background_map = "Street Map";
P3TXT.dashboard.fig_dlg_background_satellite = "Satellite";
P3TXT.dashboard.fig_dlg_background_none = "None";
P3TXT.dashboard.fig_dlg_facilities = "Facilities";
P3TXT.dashboard.fig_dlg_paths = "Paths";
P3TXT.dashboard.fig_dlg_peaks = "Peaks";
P3TXT.dashboard.fig_dlg_markers = "Markers";
P3TXT.dashboard.fig_dlg_wedges = "LISA";
P3TXT.dashboard.fig_dlg_analyses = "Isotopic";
P3TXT.dashboard.fig_dlg_fovs = "Field of View";
P3TXT.dashboard.fig_dlg_grid = "Submap Grid"

P3TXT.dashboard.facs_dlg_add_new_file = "Add new KML file for facilities layer";
P3TXT.dashboard.facs_dlg_kml_file = "KML File";
P3TXT.dashboard.facs_dlg_offsets = "Offsets";
P3TXT.dashboard.facs_ph_offsets = "LatOffset, LongOffset";
P3TXT.dashboard.facs_dlg_linewidth = "Line Width";
P3TXT.dashboard.facs_dlg_linecolor = "Line Color";
P3TXT.dashboard.facs_dlg_xpath = "XPath";

P3TXT.dashboard.markers_dlg_add_new_file = "Add new CSV file for user markers";
P3TXT.dashboard.markers_dlg_csv_file = "CSV File";

// Validator strings
P3TXT.validator_missing_parameter = "Required parameter missing: ";
P3TXT.validator_fails_transformation = "Parameter cannot be transformed, attempting to use unchanged: ";
P3TXT.validator_regex_not_matched = "Parameter does not match regex: ";
P3TXT.validator_predicate_returns_false = "Parameter fails validation test: ";
P3TXT.validator_wrong_type = "Parameter is of wrong type: ";
P3TXT.validator_invalid_latlng = "Invalid latitude, longitude pair";
P3TXT.validator_invalid_latlng_offsets = "Invalid latitude, longitude offsets";

P3TXT.dashboard.validator_empty_title = "Title must be a non-empty string";
P3TXT.dashboard.validator_invalid_start_time = "Invalid start time";
P3TXT.dashboard.validator_invalid_end_time = "Invalid end time";
P3TXT.dashboard.validator_invalid_times = "End time must be after start time";
P3TXT.dashboard.validator_no_markers_file = "No markers file";
P3TXT.dashboard.validator_no_facilities_file = "No facilities file";
P3TXT.dashboard.validator_bad_offset = "Bad offset pair";
P3TXT.dashboard.validator_offset_too_large = "Maximum absolute offset exceeded (degrees): ";
P3TXT.dashboard.validator_instructions_failed_validation = "Instructions failed validation";
P3TXT.dashboard.validator_invalid_corner_latitudes = "SW corner latitude must be less than NE corner latitude.";
P3TXT.dashboard.validator_invalid_corner_longitudes = "SW corner longitude must be less than NE corner longitude.";
P3TXT.dashboard.validator_timezone_conversion_error = "Server unresponsive - click OK again to retry.";
P3TXT.dashboard.validator_too_many_submaps = "Cannot have more than 100 submaps."
P3TXT.dashboard.validator_submaps = "Invalid submap specification."

// GETREPORT strings
P3TXT.getReport = {};
P3TXT.getReport.leftHeading = "Picarro Surveyor For Natural Gas Leak Detection";
P3TXT.getReport.firstSubmittedBy = "First submitted by";
P3TXT.getReport.firstSubmittedAt = "at";
P3TXT.getReport.figureNumber = "Figure";
P3TXT.getReport.swCorner = "SW Corner (Lat,Lng)";
P3TXT.getReport.neCorner = "NE Corner (Lat,Lng)";
P3TXT.getReport.minPeakAmpl = "Min Peak Ampl (ppm)";
P3TXT.getReport.exclusionRadius = "Excl Radius (m)";
P3TXT.getReport.baseType = "Base Type";
P3TXT.getReport.facilities = "Facilities";
P3TXT.getReport.paths = "Paths";
P3TXT.getReport.peaks = "Peaks";
P3TXT.getReport.markers = "Markers";
P3TXT.getReport.wedges = "LISAs";
P3TXT.getReport.swaths = "FOV";
P3TXT.getReport.analyses = "Isotopic";
P3TXT.getReport.heading_analyses_table = "Isotopic Analysis Table";
P3TXT.getReport.heading_peaks_table = "Peaks Table";
P3TXT.getReport.heading_runs_table = "Runs Table";
P3TXT.getReport.heading_surveys_table = "Surveys Table";
P3TXT.getReport.heading_settings_table = "Figure Settings Table";
P3TXT.getReport.dispositions = {};
P3TXT.getReport.dispositions.complete = "Complete";
P3TXT.getReport.dispositions.cancelled = "User Cancelled";
P3TXT.getReport.dispositions.uncertain = "Large Uncertainty";
P3TXT.getReport.dispositions.outside_range = "Out of Range";
P3TXT.getReport.dispositions.not_enough_data = "Insufficient Data";

// Names of colors (NEVER TRANSLATE, These are for system usage)
P3TXT.colors = {};
P3TXT.colors.black = "black";
P3TXT.colors.blue = "blue";
P3TXT.colors.cyan = "cyan";
P3TXT.colors.green = "green";
P3TXT.colors.magenta = "magenta";
P3TXT.colors.red = "red";
P3TXT.colors.white = "white";
P3TXT.colors.yelow = "yellow";

//);