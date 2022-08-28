import inspect
import socket
from typing import List
import logging
import json
from inputimeout import inputimeout, TimeoutOccurred
import threading

import objects.ParticipantObject as ParticipantObject
import objects.DDSInfo as DDSInfo
import objects.ConfigData as ConfigData


class DDSDomain:
    def __init__(
        self,
        topics,
        address_family=None,
        socket_kind=None,
        hostName="",
        port=1234,
        field_participant="field",
    ) -> None:
        """_summary_

        Args:
            topics (_type_): _description_
            address_family (_type_, optional): _description_. Defaults to None.
            socket_kind (_type_, optional): _description_. Defaults to None.
            hostName (str, optional): _description_. Defaults to "".
            port (int, optional): _description_. Defaults to 1234.
            field_participant (str, optional): _description_. Defaults to "field".
        """
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
        self.participant_list: List[ParticipantObject.ParticipantObject] = []
        self.participant_requests_count = 0
        self.field_participant_topic_name = field_participant

        # DDSInfo
        self.dds_info_object = DDSInfo.DDSInfo()

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
        logging.info("Server is starting...")

    def set_topics(self):
        self.dds_info_object.add_topic_info_from_list(topic_list=self.topics)

    # Helper Functions
    def format_msg_with_header(
        self,
        msg: str,
        header_size: int = 5,
    ):
        if not header_size:
            header_size = self.HEADERSIZE
        return bytes(f"{len(msg):<{header_size}}" + msg, "utf-8")

    def recv_msg(
        self,
        participant_socket: socket.socket,
    ) -> str:
        while True:
            len_str = participant_socket.recv(self.HEADERSIZE)
            if len_str:
                msg_len = int(len_str)
                return_str = participant_socket.recv(msg_len).decode("utf-8")
                if return_str:
                    return return_str

    def set_constants(
        self,
        fields_participant_obj: ParticipantObject,
    ):

        fields_participant_obj.participant_socket.send(
            self.format_msg_with_header("CONSTANTS")
        )
        constants_str = self.recv_msg(fields_participant_obj.participant_socket)
        self.CONSTANTS = json.loads(constants_str)
        self.constants_set = True

    def send_constants(self, participant_obj: ParticipantObject.ParticipantObject):
        while True:
            msg = self.recv_msg(participant_obj.get_participant_socket())
            if msg == "CONSTANTS":
                constants_dict = {}
                for each_constant in participant_obj.config_data.constants_required:
                    constants_dict[each_constant] = self.CONSTANTS[each_constant]
                participant_obj.get_participant_socket().send(
                    self.format_msg_with_header(json.dumps(constants_dict))
                )
                break

    def send_topic_rules(self, participant_obj: ParticipantObject.ParticipantObject):
        while True:
            msg = self.recv_msg(participant_obj.get_participant_socket())
            if msg == "TOPIC_RULES":
                participant_obj.get_participant_socket().send(
                    self.format_msg_with_header(json.dumps(participant_obj.topic_rules))
                )
                break

    def save_data_of_participant(
        self,
        participant_socket: socket.socket,
        participant_address,
        config_str: str,
    ):
        config_json = json.loads(config_str)
        config_data_obj = ConfigData.ConfigData(config_json=config_json)
        this_participant_obj = ParticipantObject.ParticipantObject(
            participant_socket=participant_socket,
            address=participant_address,
            config_data=config_data_obj,
        )
        # topic rules
        this_participant_obj.fill_rules(self.topics)

        self.dds_info_object.add_subscribed_participant(this_participant_obj)
        return this_participant_obj

    def send_info_to_subscribers(
        self,
        info: str,
        from_participant: ParticipantObject.ParticipantObject,
    ):
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
            self.constants_set = True

        # Sending Constants
        if (
            self.constants_set
            and this_participant_obj.config_data.name
            != self.field_participant_topic_name
        ):
            self.send_constants(this_participant_obj)

        # Sending topics Parameters
        self.send_topic_rules(this_participant_obj)

        # Start Analysis Procedure
        while True:
            if self.analysis_started:
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
        try:
            answer = inputimeout(
                prompt=f"{self.participant_requests_count}: To start Analysis, type'y': ",
                timeout=5,
            )
        except TimeoutOccurred:
            answer = "n"
        if answer == "y" or answer == "Y":
            self.analysis_started = True
        else:
            return

    def start_server_listening(self):

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
        print(self.server_socket)
        self.instantiate_dds()

        self.listening_thread = threading.Thread(target=self.start_server_listening)
        self.listening_thread.start()


if __name__ == "__main__":
    obj = DDSDomain(topics=[])
    parameters_list = list(inspect.signature(obj.recv_msg).parameters)
    print(parameters_list)
    print(inspect.getmembers(obj))
