def minutes_to_hhmm(minutes_total):
    hours = minutes_total // 60
    minutes = minutes_total % 60
    return "%d:%02d" % (hours, minutes)
