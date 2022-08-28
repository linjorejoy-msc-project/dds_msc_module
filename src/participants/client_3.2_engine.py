from objects.Participant import Participant
import logging
import json

config = {
    "id": "CLIENT_2",
    "name": "engine",
    "subscribed_topics": ["fuel_flow", "field"],
    "non_essential_subscribed_topics": [],
    "published_topics": ["thrust"],
    "constants_required": [
        "requiredThrust",
        "specificImpulse",
        "gravitationalAcceleration",
        "timestepSize",
        "totalTimesteps",
    ],
    "variables_subscribed": [],
}
init_topic_data = {"currentThrust": 0}

engine_participant = Participant(
    CONFIG_DATA=config,
    topic_data=init_topic_data,
    will_initiate=True,
)

# Actual Analysis
def run_one_cycle_ow():
    engine_participant.topic_data["currentThrust"] = (
        engine_participant.CONSTANTS["specificImpulse"]
        * engine_participant.CONSTANTS["gravitationalAcceleration"]
        * engine_participant.data_dict["currentMassFlowRate"]
    )
    logging.info(f"Received {engine_participant.data_dict=}")
    logging.info(
        f"Timestep: {engine_participant.data_dict['currentTimestep']:5}-{engine_participant.topic_data}"
    )
    engine_participant.send_topic_data(
        engine_participant.server_socket,
        "thrust",
        json.dumps(engine_participant.topic_data),
    )


def fill_init_topic_data_ow():
    engine_participant.topic_data["currentThrust"] = engine_participant.CONSTANTS[
        "requiredThrust"
    ]


def start_initiation_ow():
    engine_participant.send_topic_data(
        engine_participant.server_socket,
        "thrust",
        json.dumps(engine_participant.topic_data),
    )


engine_participant.run_one_cycle = run_one_cycle_ow
engine_participant.fill_init_topic_data = fill_init_topic_data_ow
engine_participant.start_initiation = start_initiation_ow
engine_participant.main()
