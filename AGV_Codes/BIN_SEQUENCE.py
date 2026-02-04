now = time.time()

if pickup_state == "APPROACH":
    if now - pickup_start_time > PICKUP_TIMING["APPROACH"]:
        motor.send("V_DOWN")
        pickup_state = "DOWN"
        pickup_start_time = now
        log_cmd("PICKUP → DOWN")

elif pickup_state == "DOWN":
    if now - pickup_start_time > PICKUP_TIMING["DOWN"]:
        motor.send("GRIP_CLOSE")
        pickup_state = "GRAB"
        pickup_start_time = now
        log_cmd("PICKUP → GRAB")

elif pickup_state == "GRAB":
    if now - pickup_start_time > PICKUP_TIMING["GRAB"]:
        motor.send("V_UP")
        pickup_state = "UP"
        pickup_start_time = now
        log_cmd("PICKUP → UP")

elif pickup_state == "UP":
    if now - pickup_start_time > PICKUP_TIMING["UP"]:
        motor.send("H_BACK")
        pickup_state = "RETRACT"
        pickup_start_time = now
        log_cmd("PICKUP → RETRACT")

elif pickup_state == "RETRACT":
    if now - pickup_start_time > PICKUP_TIMING["RETRACT"]:
        motor.send(f"FLIP_{bin_type}")
        pickup_state = "FLIP"
        pickup_start_time = now
        log_cmd(f"PICKUP → FLIP {bin_type}")

elif pickup_state == "FLIP":
    if now - pickup_start_time > PICKUP_TIMING["FLIP"]:
        motor.send("FLIP_NEUTRAL")
        pickup_state = "DONE"
        log_cmd("PICKUP → DONE")

