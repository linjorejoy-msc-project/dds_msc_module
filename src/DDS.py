import socket
import threading
import json
import time
import datetime
import logging
from typing import Any, Dict, List, Tuple
from inputimeout import inputimeout, TimeoutOccurred


FORMAT = "%(levelname)-10s %(asctime)s: %(message)s"
logging.basicConfig(
    handlers=[
        logging.FileHandler(filename="src/LOGS/logs.log", encoding="utf-8", mode="w")
    ],
    level=logging.DEBUG,
    format=FORMAT,
)


class MessageData:
    def __init__(self) -> None:
        self.from_participant = None
        self.topic = None
        self.msg = None


class ConfigData:
    def __init__(
        self,
        config_json: dict = {},
        id: str = "",
        name: str = "",
        subscribed_topics: List[str] = [],
        non_essential_subscribed_topics: List[str] = [],
        published_topics: List[str] = [],
        constants_required: List[str] = [],
        variables_subscribed: List[str] = [],
    ) -> None:
        if config_json:
            self.id = config_json["id"]
            self.name = config_json["name"]
            self.subscribed_topics = config_json["subscribed_topics"]
            self.non_essential_subscribed_topics = config_json[
                "non_essential_subscribed_topics"
            ]
            self.published_topics = config_json["published_topics"]
            self.constants_required = config_json["constants_required"]
            self.variables_subscribed = config_json["variables_subscribed"]
        else:
            self.id = id
            self.name = name
            self.subscribed_topics = subscribed_topics
            self.non_essential_subscribed_topics = non_essential_subscribed_topics
            self.published_topics = published_topics
            self.constants_required = constants_required
            self.variables_subscribed = variables_subscribed


class ParticipantObject:
    def __init__(
        self,
        participant_socket: socket.socket,
        address,
        config_data: ConfigData,
    ) -> None:
        self.participant_socket = participant_socket
        self.address = address
        self.config_data = config_data
        self.topics_subscribed = []
        self.topic_rules = []

        # initial setup
        self.fill_topics_subscribed()
        # self.fill_rules()

    def get_participant_socket(self):
        return self.participant_socket

    def fill_topics_subscribed(self):
        self.topics_subscribed = self.config_data.subscribed_topics

    def fill_rules(self, full_topic_data: List[Dict[str, Any]]):
        self.topic_rules = [
            topic_info
            for topic_info in full_topic_data
            if self.is_subscribed_to_topic(topic_info["name"])
        ]

    def is_subscribed_to_topic(self, topic: str):
        return topic in self.config_data.subscribed_topics


class Topic:
    # This is topic data stored by DDSDomain object in DDSInfo Object
    def __init__(self, topic_name: str, parameters_required=[]) -> None:
        self.topic_name = topic_name
        self.regex_format = ""
        self.subscribed_participants: List[ParticipantObject] = []
        self.messages: List[MessageData] = []
        self.parameters_required = parameters_required

    def add_subscribed_participant(self, participant: ParticipantObject):
        # TODO
        self.subscribed_participants.append(participant)

    def get_subscribed_participants(self):
        return self.subscribed_participants


class DDSInfo:
    def __init__(self) -> None:
        self.topics: List[Topic] = []
        self.participants: List[ParticipantObject] = []

    def get_participant_list(self):
        return self.participants

    def get_participant_by_socket(self):
        pass

    def add_subscribed_participant(self, participant: ParticipantObject):
        self.participants.append(participant)
        self.add_participant_info_to_topics(participant)

    def remove_subscribed_participant(self, participant: ParticipantObject):
        self.participants.remove(participant)

    def add_topic_info_from_list(self, topic_list: List[Dict[str, Any]]):
        for topic_dict in topic_list:
            logging.info(f"{topic_dict} conveted to object")
            this_topic_obj = Topic(topic_dict["name"])
            this_topic_obj.regex_format = topic_dict["regex"]
            this_topic_obj.parameters_required = (
                topic_dict["parameters_present"]
                if "parameters_present" in topic_dict.keys()
                else []
            )
            self.topics.append(this_topic_obj)

    def get_topic_by_name(self, name: str):
        for topic in self.topics:
            if topic.topic_name == name:
                return topic
        return

    def add_participant_info_to_topics(self, participant: ParticipantObject):
        for topic_name in participant.config_data.subscribed_topics:
            this_topic_obj = self.get_topic_by_name(topic_name)
            if this_topic_obj:
                this_topic_obj.add_subscribed_participant(participant)
            else:
                print(f"{topic_name} does not have a topic object")


class DDSDomain:
    def __init__(
        self,
        address_family=None,
        socket_kind=None,
        hostName="",
        port=1234,
        topics={},
        field_participant="field",
    ) -> None:
        # Connectivity
        self.address_family = address_family
        self.socket_kind = socket_kind
        self.hostName = hostName
        self.port = port
        self.server_socket = None

        # Data transmission constants
        self.HEADERSIZE = 5
        self.BUFFERSIZE = 32

        # Constants
        self.CONSTANTS = {}
        self.constants_set = False
        self.analysis_started = False
        self.topics = topics

        # Participants
        self.participant_list: List[ParticipantObject] = []
        self.participant_requests_count = 0
        self.field_participant_topic_name = field_participant

        # DDSInfo
        self.dds_info_object = DDSInfo()

        # Threads
        self.listening_thread = None

    def start_server(
        self,
        addressFamily=socket.AF_INET,
        socketKind=socket.SOCK_STREAM,
        hostName=socket.gethostname(),
        port: int = 1234,
    ):
        new_socket = socket.socket(
            addressFamily if addressFamily else socket.AF_INET,
            socketKind if socketKind else socket.SOCK_STREAM,
        )
        new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        new_socket.bind((hostName, port))
        new_socket.listen(5)
        return new_socket

    def log_initial_setup(self):
        print("Server is starting...")
        pass

    def set_topics(self):
        self.dds_info_object.add_topic_info_from_list(topic_list=self.topics)

    # Helper Functions
    def format_msg_with_header(self, msg: str, header_size: int = 5):
        if not header_size:
            header_size = self.HEADERSIZE
        return bytes(f"{len(msg):<{header_size}}" + msg, "utf-8")

    def recv_msg(self, participant_socket: socket.socket) -> str:
        while True:
            len_str = participant_socket.recv(self.HEADERSIZE)
            if len_str:
                msg_len = int(len_str)
                return_str = participant_socket.recv(msg_len).decode("utf-8")
                if return_str:
                    return return_str

    def set_constants(self, fields_participant_obj: ParticipantObject):
        global constants_set
        global CONSTANTS

        fields_participant_obj.participant_socket.send(
            self.format_msg_with_header("CONSTANTS")
        )
        constants_str = self.recv_msg(fields_participant_obj.participant_socket)
        CONSTANTS = json.loads(constants_str)
        constants_set = True

    def send_constants(self, participant_obj: ParticipantObject):
        while True:
            msg = self.recv_msg(participant_obj.get_participant_socket())
            if msg == "CONSTANTS":
                constants_dict = {}
                for each_constant in participant_obj.config_data.constants_required:
                    constants_dict[each_constant] = CONSTANTS[each_constant]
                participant_obj.get_participant_socket().send(
                    self.format_msg_with_header(json.dumps(constants_dict))
                )
                break

    def send_topic_rules(self, participant_obj: ParticipantObject):
        while True:
            msg = self.recv_msg(participant_obj.get_participant_socket())
            if msg == "TOPIC_RULES":
                constants_dict = {}
                for each_constant in participant_obj.config_data.constants_required:
                    constants_dict[each_constant] = CONSTANTS[each_constant]
                participant_obj.get_participant_socket().send(
                    self.format_msg_with_header(json.dumps(constants_dict))
                )
                break

    def save_data_of_participant(
        self,
        participant_socket: socket.socket,
        participant_address,
        config_str: str,
    ):
        config_json = json.loads(config_str)
        config_data_obj = ConfigData(config_json=config_json)
        this_participant_obj = ParticipantObject(
            participant_socket=participant_socket,
            address=participant_address,
            config_data=config_data_obj,
        )
        # topic rules
        this_participant_obj
        self.dds_info_object.add_subscribed_participant(this_participant_obj)
        return this_participant_obj

    def send_info_to_subscribers(self, info: str, from_participant: ParticipantObject):
        topic = info[:25].strip()

        topic_obj = self.dds_info_object.get_topic_by_name(topic)

        if topic_obj:
            logging.info(f"{self.format_msg_with_header(info)=}\nsent to subscribers")
            for each_participant in topic_obj.get_subscribed_participants():
                each_participant.get_participant_socket().send(
                    self.format_msg_with_header(info)
                )
        else:
            logging.error(f"The topic: {topic} does not have an object")

    # DDS Funcs

    def handle_participant(
        self,
        participant_socket: socket.socket,
        participant_address,
    ):
        global analysis_started
        global constants_set

        # Send Config
        participant_socket.send(self.format_msg_with_header("CONFIG"))
        config_str = self.recv_msg(participant_socket)

        # save data of participant
        this_participant_obj = self.save_data_of_participant(
            participant_socket, participant_address, config_str
        )

        # Setting Constants
        if this_participant_obj.config_data.name == self.field_participant_topic_name:
            self.set_constants(this_participant_obj)
            constants_set = True

        # Sending Constants
        if (
            constants_set
            and this_participant_obj.config_data.name
            != self.field_participant_topic_name
        ):
            self.send_constants(this_participant_obj)

        # Sending topics Parameters

        # Start Analysis Procedure
        while True:
            if analysis_started:
                this_participant_obj.get_participant_socket().send(
                    self.format_msg_with_header("START")
                )
                break

        # Start Analysis
        logging.info(
            f"Analysis while loop started for {this_participant_obj.config_data.name}"
        )
        while True:
            info = self.recv_msg(this_participant_obj.get_participant_socket())
            self.send_info_to_subscribers(info, this_participant_obj)

    def request_analysis_start(self):
        global analysis_started
        try:
            answer = inputimeout(prompt=f"To start Analysis, type'y': ", timeout=5)
        except TimeoutOccurred:
            answer = "n"
        if answer == "y" or answer == "Y":
            analysis_started = True
        else:
            return

    def start_server_listening(self):
        global server_socket

        logging.info("start_server_listening while loop started")
        while not self.analysis_started:
            # New Participant
            new_participant, new_participant_address = self.server_socket.accept()

            # logging and keeping count
            self.participant_requests_count += 1
            logging.info(f"Found {new_participant_address}: {new_participant}")

            # new thread for participant
            this_participant_thread = threading.Thread(
                target=self.handle_participant,
                args=(
                    new_participant,
                    new_participant_address,
                ),
            )
            this_participant_thread.start()

            self.request_analysis_start()

    def instantiate_dds(self):
        self.log_initial_setup()
        self.set_topics()

    def main(self):
        self.server_socket = self.start_server(
            hostName="",
        )
        self.instantiate_dds()

        self.listening_thread = threading.Thread(target=self.start_server_listening)
        self.listening_thread.start()


class Participant:
    def __init__(
        self,
        CONFIG_DATA: Dict,
        address: str = "localhost",
        port: int = 1234,
        topic_data: Dict = {},
        cycle_flags_func_list: List = None,
    ) -> None:

        # Config
        self.CONFIG_DATA = CONFIG_DATA

        # Connectivity
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((address, port))

        # Constants to receive from DDS domain
        self.CONSTANTS = {}
        self

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
        self.topic_func_dict = {
            "drag": 0,
            "thrust": 0,
            "fuel_flow": 0,
            "field": 0,
            "motion": 0,
            "atmosphere": 0,
        }

        if cycle_flags_func_list:
            self.fill_flags_dict(cycle_flags_func_list)
        else:
            self.fill_flags_dict(self.CONFIG_DATA["subscribed_topics"])

    def fill_init_topic_data(self):
        pass

    def run_updation_func(self, topic):
        pass

    def run_cycle(self):
        while True:
            if self.check_to_run_cycle(cycle_flags):
                self.make_all_cycle_flags_default(cycle_flags)
                self.run_one_cycle()

    def run_one_cycle(self):
        pass

    def listen_analysis(self):
        global data_dict
        global cycle_flags
        global topic_data

        while True:
            topic, sent_time, recv_time, info = self.recv_topic_data(self.server_socket)
            if topic in cycle_flags.keys():
                cycle_flags[topic] = True
                self.topic_func_dict[topic](data_dict, sent_time, recv_time, info)
            elif topic:
                self.run_updation_func(topic)
            else:
                print(f"{self.CONFIG_DATA['name']} is not subscribed to {topic}")

    def listening_function(self):
        while True:
            try:
                msg = self.recv_msg(self.server_socket)
                if msg == "CONFIG":
                    self.send_config(self.server_socket, self.CONFIG_DATA)
                    self.CONSTANTS = self.request_constants(self.server_socket)
                    # Topic rules request
                    self.topic_data_rules = self.request_topic_rules()
                    self.fill_init_topic_data()
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

    # Helpers

    def format_msg_with_header(self, msg: str, header_size: int = 5):
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

    def request_topic_rules(self):
        server_socket.send(self.format_msg_with_header("TOPIC_RULES"))
        topic_rules_received = self.recv_msg(server_socket)
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
                    msg[self.TOPICLABELSIZE: self.TOPICLABELSIZE + self.TIMEDATASIZE]
                ).strip()
            ),
            self.get_current_time(),
            msg[self.TOPICLABELSIZE + self.TIMEDATASIZE:],
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

    def recv_msg(self) -> str:
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


if __name__ == "__main__":
    topics = [
        {"name": "fuel_flow", "regex": ""},
        {"name": "thrust", "regex": ""},
        {"name": "drag", "regex": ""},
        {"name": "motion", "regex": ""},
        {"name": "field", "regex": ""},
        {"name": "atmosphere", "regex": ""},
        {"name": "field_update", "regex": ""},
        {"name": "field_update_realtime", "regex": ""},
        {"name": "motion_update_realtime", "regex": ""},
        {"name": "fuel_flow_update_realtime", "regex": ""},
    ]
    dds_obj = DDSDomain(topics=topics)
    dds_obj.main()
