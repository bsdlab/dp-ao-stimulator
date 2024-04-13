import pylsl

from fire import Fire

import numpy as np


SIM_SFREQ_HZ = 100

SWITCH_FREQ_HZ = 2

def get_data(high_val: float = 150) -> np.ndarray:
    data = np.zeros(SIM_SFREQ_HZ * 6000)

    high_seq_len = int(np.round(SIM_SFREQ_HZ / (2 * SWITCH_FREQ_HZ)))

    i = high_seq_len
    while i < len(data):
        data[i:(i + high_seq_len)] = high_val
        i += 2 * high_seq_len
        

    return data


def main(stream_name="control_signal"):
    data = get_data()
    info = pylsl.StreamInfo(
        stream_name,
        "EEG", 1, SIM_SFREQ_HZ, "float32", "myuidtest"
    )
    outlet = pylsl.StreamOutlet(info)

    # Send data
    start_time = pylsl.local_clock()
    sent_samples = 0
    i = 0
    while True:
        elapsed_time = pylsl.local_clock() - start_time

        required_samples = int(SIM_SFREQ_HZ * elapsed_time) - sent_samples
        if required_samples > 0:
            stamp = pylsl.local_clock()
            outlet.push_chunk(list(data[i: i+required_samples]), stamp)
            sent_samples += required_samples

            i += required_samples

            # loop over again
            if i + 10 * required_samples > len(data):
                i = 0


if __name__ == "__main__":
    Fire(main)
