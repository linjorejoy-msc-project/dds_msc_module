import logging
import socket
from typing import List, Dict, Any

import objects.ParticipantObject as ParticipantObject
import objects.Topic as Topic


class DDSInfo:
    def __init__(self) -> None:
        self.topics: List[Topic.Topic] = []
        self.participants: List[ParticipantObject.ParticipantObject] = []

    def get_participant_list(self) -> List[ParticipantObject.ParticipantObject]:
        return self.participants

    def get_participant_by_socket(self, participant_socket: socket.socket):
        pass

    def add_subscribed_participant(self, participant: ParticipantObject):
        self.participants.append(participant)
        self.add_participant_info_to_topics(participant)

    def remove_subscribed_participant(self, participant: ParticipantObject):
        self.participants.remove(participant)

    def add_topic_info_from_list(
        self,
        topic_list: List[Dict[str, Any]],
    ):
        for topic_dict in topic_list:
            logging.info(f"{topic_dict} conveted to object")
            this_topic_obj = Topic.Topic(topic_dict["name"])
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
