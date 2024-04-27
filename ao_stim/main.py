import time
import serial
import socket
import pylsl
import threading
import tomllib
import pylsl

from fire import Fire
from dareplane_utils.stream_watcher.lsl_stream_watcher import StreamWatcher
from dareplane_utils.logging.logger import get_logger
from dareplane_utils.general.time import sleep_s

logger = get_logger("ao_stim")

# --- Stim paramters
# StimChannel
# FirstPhaseDelay_mS
# FirstPhaseAmpl_mA
# FirstPhaseWidth_mS
# SecondPhaseDelay_mS
# SecondPhaseAmpl_mA
# SecondPhaseWidth_mS
# Freq_hZ
# Duration_sec
# ReturnChannel
# For a single stimulation pulse
STIM_ON = "STARTSTIM|10272|0|-1|0.36|0|1|0.36|130|0.006|10273"


def init_lsl_outlet() -> pylsl.StreamOutlet:
    n_channels = 1
    info = pylsl.StreamInfo(
        "ao_cmd",
        "Marker",
        n_channels,
        0,  # srate = 0 --> irregular stream
        "int32",
    )

    # enrich a channel name
    chns = info.desc().append_child("channels")
    ch = chns.append_child("channel")
    ch.append_child_value("label", "ao_stim")
    ch.append_child_value("unit", "AU")
    ch.append_child_value("type", "arduino_stim")
    ch.append_child_value("scaling_factor", "1")

    outlet = pylsl.StreamOutlet(info)

    return outlet


def connect_stream_watcher(config: dict) -> StreamWatcher:
    sw = StreamWatcher(
        config["stream_to_query"]["stream"],
        buffer_size_s=config["stream_to_query"]["buffer_size_s"],
    )
    sw.connect_to_stream()

    return sw


def lsl_delay(dt_us: int = 0):
    tstart = pylsl.local_clock()
    while pylsl.local_clock() - tstart < dt_us / 1e6:
        pass


def main(
    stop_event: threading.Event = threading.Event(), logger_level: int = 10
):
    logger.setLevel(logger_level)
    config = tomllib.load(open("./configs/ao_stim_config.toml", "rb"))

    # Connect to app first to start the streaming from ao-communication
    ao_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ao_sock.connect((config["ao_api"]["ip"], config["ao_api"]["port"]))

    sw = connect_stream_watcher(config)

    outlet = init_lsl_outlet()

    last_val = 0

    tlast = time.perf_counter_ns()
    dt_us = 100

    # for hardware trigger - just for double checking
    triggerbox = serial.Serial(port="COM4")
    imax = 255
    i = 0

    try:
        while not stop_event.is_set() and triggerbox is not None:
            # limit the update rate
            if time.perf_counter_ns() - tlast > dt_us * 1e3:
                preupdate = time.perf_counter_ns()
                sw.update()
                dt_ms = (time.perf_counter_ns() - tlast) / 1e6

                if (
                    sw.n_new > 0
                    and dt_ms > config["stimulation"]["grace_period_ms"]
                ):

                    val = sw.unfold_buffer()[-1]

                    if val != last_val and len(val) == 1:
                        ival = int(val[0])
                        if ival > 127:
                            ao_sock.sendall(STIM_ON.encode())

                        outlet.push_sample([ival])

                        # Write and reset
                        triggerbox.write([i])
                        triggerbox.write([0])
                        i = (i + 1) % imax + 1

                        sw.n_new = 0
                        last_val = val
                        tlast = time.perf_counter_ns()

                        sleep_s(dt_us * 1e-6 * 0.9)
    finally:
        triggerbox.close()
        ao_sock.close()


def get_main_thread() -> tuple[threading.Thread, threading.Event]:
    stop_event = threading.Event()
    stop_event.clear()

    thread = threading.Thread(target=main, kwargs={"stop_event": stop_event})
    thread.start()

    return thread, stop_event


def write_and_read(arduino: serial.Serial, message: str):
    tpre = time.time_ns()

    while time.time_ns() - tpre < 10_000_000_000:
        arduino.write("u\n".encode())
        arduino.write("d\n".encode())
    # l = arduino.readline()
    # #
    # tfirst = time.time_ns()
    # print(f"{tfirst-tpre=}")
    # l2 = arduino.readline()
    # tsecond = time.time_ns()
    #
    # l = l.decode()
    # l2 = l2.decode()
    #
    # retstr = f"{l=} {l2=} {tsecond-tfirst=} {tfirst-tpre=} {tsecond-tpre=}"
    # print(retstr)


# In [89]: %timeit arduino.write('u'.encode())
# 520 µs ± 19.7 ns per loop (mean ± std. dev. of 7 runs, 1,000 loops ea
# ch)
# Also the full cycle seems to be about 520us as tested with the oscilloscope and this:
#
# while time.time_ns() - tpre < 10_000_000_000:
#     arduino.write('u'.encode())
#     arduino.write('d'.encode())

if __name__ == "__main__":
    Fire(main)
