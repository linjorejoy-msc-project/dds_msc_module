import socket
import objects.ConfigData as ConfigData
from typing import List, Dict, Any


class ParticipantObject:
    def __init__(
        self,
        participant_socket: socket.socket,
        address,
        config_data: ConfigData.ConfigData,
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
        return (
            topic in self.config_data.subscribed_topics
            or topic in self.config_data.non_essential_subscribed_topics
        )
