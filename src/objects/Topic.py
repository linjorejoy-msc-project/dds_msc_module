import objects.ParticipantObject as ParticipantObject
import objects.MessageData as MessageData
from typing import List


class Topic:
    # This is topic data stored by DDSDomain object in DDSInfo Object
    def __init__(self, topic_name: str, parameters_required=[]) -> None:
        self.topic_name = topic_name
        self.regex_format = ""
        self.subscribed_participants: List[ParticipantObject.ParticipantObject] = []
        self.messages: List[MessageData.MessageData] = []
        self.parameters_required = parameters_required

    def add_subscribed_participant(self, participant: ParticipantObject):
        # TODO
        self.subscribed_participants.append(participant)

    def get_subscribed_participants(self):
        return self.subscribed_participants
