from fire import Fire

from dareplane_utils.default_server.server import DefaultServer
from ao_stim.main import get_main_thread


def main(port: int = 8080, ip: str = "127.0.0.1", loglevel: int = 10):
    # logger.setLevel(loglevel)

    pcommand_map = {
        "START": get_main_thread  # note: that this will return a thread and an according stop_event, the default server will be able to do the bookkeeping including stopping the thread when STOP or CLOSE are called
    }

    server = DefaultServer(
        port, ip=ip, pcommand_map=pcommand_map, name="ao_stim_server"
    )

    # initialize to start the socket
    server.init_server()
    # start processing of the server
    server.start_listening()

    return 0


if __name__ == "__main__":
    Fire(main)
