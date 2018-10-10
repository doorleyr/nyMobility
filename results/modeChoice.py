def predictModeProbs():
    if trip_leg_miles <= 0.6800000071525574:
        if trip_leg_miles <= 0.2854999899864197:
            if trip_leg_miles <= 0.04349999874830246:
                return [0.02, 0.41, 0.57, 0.03]
            else:  # if trip_leg_miles > 0.04349999874830246
                return [0.05, 0.08, 0.87, 0.01]
        else:  # if trip_leg_miles > 0.2854999899864197
            if motif_HWWH <= 0.5:
                return [0.15, 0.25, 0.56, 0.04]
            else:  # if motif_HWWH > 0.5
                return [0.0, 0.85, 0.14, 0.02]
    else:  # if trip_leg_miles > 0.6800000071525574
        if trip_leg_miles <= 4.67549991607666:
            if hh_lifeCycle <= 5.5:
                return [0.19, 0.5, 0.09, 0.22]
            else:  # if hh_lifeCycle > 5.5
                return [0.48, 0.17, 0.11, 0.24]
        else:  # if trip_leg_miles > 4.67549991607666
            if motif_HOOH <= 0.5:
                return [0.3, 0.07, 0.01, 0.62]
            else:  # if motif_HOOH > 0.5
                return [0.51, 0.17, 0.01, 0.31]
