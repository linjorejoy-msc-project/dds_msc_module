import time, datetime, threading
from typing import List, Dict, Tuple
import socket
import json


class Participant:
    def __init__(
        self,
        CONFIG_DATA: Dict,
        address: str = "localhost",
        port: int = 1234,
        topic_data: Dict = {},
        cycle_flags_func_list: List = None,
        is_field_participant=False,
        CONSTANTS={},
        will_initiate=False,
    ) -> None:

        # Config
        self.CONFIG_DATA = CONFIG_DATA

        # Connectivity
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((address, port))

        # Constants to receive from DDS domain
        self.CONSTANTS = CONSTANTS if CONSTANTS else {}
        self.is_field_participant = is_field_participant
        self.will_initiate = will_initiate

        # Data transmission constants
        self.HEADERSIZE = 5
        self.BUFFERSIZE = 32
        self.TOPICLABELSIZE = 25
        self.TIMEDATASIZE = 20

        self.topic_data = topic_data
        self.data_dict = {}
        self.all_data_dict = {}

        self.cycle_flags = {}

        # TODO: make common func
        self.topic_data_rules: List[Dict] = []
        self.topic_func_dict = {
            "drag": {},
            "thrust": {},
            "fuel_flow": {},
            "field": {},
            "motion": {},
            "atmosphere": {},
        }

        if cycle_flags_func_list:
            self.fill_flags_dict(cycle_flags_func_list)
        else:
            self.fill_flags_dict(self.CONFIG_DATA["subscribed_topics"])

    # Helpers

    def format_msg_with_header(
        self,
        msg: str,
        header_size: int = 5,
    ):
        if not header_size:
            header_size = self.HEADERSIZE
        return bytes(f"{len(msg):<{header_size}}" + msg, "utf-8")

    def send_config(self, config: dict):
        # logging.info(f"Sending config \n{config=}")
        self.server_socket.send(self.format_msg_with_header(json.dumps(config)))

    def request_constants(self):
        self.server_socket.send(self.format_msg_with_header("CONSTANTS"))
        constants_received = self.recv_msg(self.server_socket)
        return json.loads(constants_received)

    def send_constants(self):
        self.server_socket.send(self.format_msg_with_header(json.dumps(self.CONSTANTS)))

    def request_topic_rules(self):
        self.server_socket.send(self.format_msg_with_header("TOPIC_RULES"))
        topic_rules_received = self.recv_msg(self.server_socket)
        return json.loads(topic_rules_received)

    def check_to_run_cycle(self, cycle_flags: dict):
        if cycle_flags:
            return all(cycle_flags.values())
        else:
            return False

    def make_all_cycle_flags_default(self, cycle_flags: dict):
        for key in cycle_flags.keys():
            cycle_flags[key] = False

    def recv_topic_data(self) -> Tuple[str, int, int, str]:
        msg = self.recv_msg(self.server_socket)

        return (
            str(msg[: self.TOPICLABELSIZE]).strip(),
            int(
                str(
                    msg[self.TOPICLABELSIZE : self.TOPICLABELSIZE + self.TIMEDATASIZE]
                ).strip()
            ),
            self.get_current_time(),
            msg[self.TOPICLABELSIZE + self.TIMEDATASIZE :],
        )

    def send_topic_data(self, topic: str, data: str):
        msgToSend = f"{topic:{self.TOPICLABELSIZE}}{str(int(self.get_current_time())):{self.TIMEDATASIZE}}{data}"
        formatted_msg = self.format_msg_with_header(msgToSend)
        self.server_socket.send(formatted_msg)

    def get_current_time(self):
        return int(
            (
                datetime.datetime.now().hour * 60 * 60
                + datetime.datetime.now().minute * 60
                + datetime.datetime.now().second
            )
            * 1000
            + datetime.datetime.now().microsecond / 1000
        )

    def recv_msg(self, server_socket) -> str:
        try:
            while True:
                len_str = self.server_socket.recv(self.HEADERSIZE)
                if len_str:
                    recv_time = time.perf_counter_ns()
                    msg_len = int(len_str)
                    return_str = self.server_socket.recv(msg_len).decode("utf-8")
                    if return_str:
                        return return_str
        except Exception as e:
            print(f"Error Occured\n{e}")
            return None

    def fill_flags_dict(self, topics_list):
        self.cycle_flags
        for topic in topics_list:
            self.cycle_flags[topic] = False

    def fill_topic_data_rules(self):
        for rule in self.topic_data_rules:
            self.topic_func_dict[rule["name"]] = rule

    def topic_funcs(
        self,
        topic: str,
        data_dict: Dict,
        sent_time: int,
        recv_time: int,
        info: Dict,
    ):
        for param in self.topic_func_dict[topic]["parameters_present"]:
            if self.topic_func_dict[topic]["parameters_present"] == "receive":
                data_dict[param] = info[param]
        data_dict["sent_time_ns"] = sent_time
        data_dict["recv_time_ns"] = recv_time
        data_dict["latency_ms"] = recv_time - sent_time

    # Analysis Funs
    def start_initiation(self):
        # Overwrite if necessary
        pass

    def fill_init_topic_data(self):
        # Need to overwrite
        pass

    def run_updation_func(self, topic):
        pass

    def run_one_cycle(self):
        # Need to overwrite
        pass

    def run_cycle(self):
        if self.will_initiate:
            self.start_initiation()
        while True:
            if self.check_to_run_cycle(self.cycle_flags):
                self.make_all_cycle_flags_default(self.cycle_flags)
                self.run_one_cycle()

    def listen_analysis(self):

        while True:
            topic, sent_time, recv_time, info = self.recv_topic_data()
            if topic in self.cycle_flags.keys():
                self.cycle_flags[topic] = True
                self.topic_funcs(topic, self.data_dict, sent_time, recv_time, info)
            elif topic:
                self.run_updation_func(topic)
            else:
                print(f"{self.CONFIG_DATA['name']} is not subscribed to {topic}")

    def listening_function(self):
        while True:
            try:
                msg = self.recv_msg(self.server_socket)
                if msg == "CONFIG":
                    self.send_config(self.CONFIG_DATA)
                    self.CONSTANTS = self.request_constants()
                    # Topic rules request
                    self.topic_data_rules = self.request_topic_rules()
                    self.fill_topic_data_rules()
                    self.fill_init_topic_data()
                elif msg == "CONSTANTS":
                    if self.is_field_participant:
                        self.send_constants()
                elif msg == "START":
                    analysis_listening_thread = threading.Thread(
                        target=self.listen_analysis
                    )
                    analysis_listening_thread.start()
                    break
            except Exception as e:
                print(f"Error Occured\n{e}")
                break
        self.run_cycle()

    def main(self):
        self.listening_function()
