nmea_templates={
'$GPRMC':['gptime',     #GPS time hhmmss.ss
           'gpstatus',  #GPS status - V or A
           'latitude',  #Current Latitude
           'NS',        #N or S
           'longitude', #Current Longitude
           'EW',        #E or W
           'speed',     #Speed over ground
           'track',     #Track made good
           'date',      #GPS date
           (None and 'magvar'), #Magnetic Variation
           (None and 'magvar_EW') #East or West
           ],
 '$GPRMB':['navstatus',     #Navigation status A or V
           (None and 'cterror'), #Cross-track error
           'dir_to_steer',  #Direction to steer - R or L
           (None and 'from_wpt'), #FROM waypoint name
           'wpt',           #Waypoint name
           'wptlat',        #Waypoint position latitude
           'wptlat_NS',     #Waypoint latitude N or S
           'wptlong',       #Waypoint position longitude
           'wptlong_EW',    #Waypoint longtitude N or W
           'dist_wpt',      #Distance to waypoint
           'brg_wpt',       #Bearing to waypoint
           'cv_wpt',        #Closing velocity knots
           'arrival'],      #Arrival circle: A-inside, V-not yet
'$PGRMZ':['altitude', #Altitude in feet
          None, None],
'$PGRME':['ehperror', #Estimated horizontal position error
          None, None, None, None, None],
'$SDDBT':['depthf', #Depth in feet
          None,
          'depthm', #Depth in meters
          None,
          'depthF', #Depth in fathoms
          None],
'$SDMTW':['temperature', #Water temperature
          None]}
