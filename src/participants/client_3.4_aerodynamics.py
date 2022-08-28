from objects.Participant import Participant
import logging
import json

config = {
    "id": "CLIENT_4",
    "name": "aerodynamics",
    "subscribed_topics": ["motion", "atmosphere", "field"],
    "non_essential_subscribed_topics": [],
    "published_topics": ["drag", "field_update"],
    "constants_required": [
        "dragCoefficient",
        "rocketFrontalArea",
        "timestepSize",
        "totalTimesteps",
    ],
    "variables_subscribed": [],
}
init_topic_data = {"drag": 0}

aerodynamics_participant = Participant(
    CONFIG_DATA=config, topic_data=init_topic_data, will_initiate=True
)

# Actual Analysis
def run_one_cycle_ow():
    aerodynamics_participant.topic_data["drag"] = (
        aerodynamics_participant.CONSTANTS["dragCoefficient"]
        * aerodynamics_participant.data_dict["density"]
        * aerodynamics_participant.data_dict["currentVelocity"]
        * aerodynamics_participant.data_dict["currentVelocity"]
        * aerodynamics_participant.CONSTANTS["rocketFrontalArea"]
        / 2
    )
    logging.info(f"Received {aerodynamics_participant.data_dict=}")
    aerodynamics_participant.send_topic_data(
        aerodynamics_participant.server_socket,
        "drag",
        json.dumps(aerodynamics_participant.topic_data),
    )
    aerodynamics_participant.send_topic_data(
        aerodynamics_participant.server_socket,
        "field_update",
        json.dumps(
            {
                "currentTimestep": aerodynamics_participant.data_dict["currentTimestep"]
                + 1,
                "currentTime": aerodynamics_participant.CONSTANTS["timestepSize"]
                * (aerodynamics_participant.data_dict["currentTimestep"] + 1),
                "totalTimestepsRun": aerodynamics_participant.data_dict[
                    "totalTimestepsRun"
                ]
                + 1,
                "versions": aerodynamics_participant.data_dict["versions"],
            }
        ),
    )
    logging.info(
        f"Timestep: {aerodynamics_participant.data_dict['currentTimestep']:5}-{aerodynamics_participant.topic_data}"
    )


def start_initiation_ow():
    aerodynamics_participant.send_topic_data(
        aerodynamics_participant.server_socket,
        "drag",
        json.dumps(aerodynamics_participant.topic_data),
    )


aerodynamics_participant.run_one_cycle = run_one_cycle_ow
aerodynamics_participant.start_initiation = start_initiation_ow
aerodynamics_participant.main()
