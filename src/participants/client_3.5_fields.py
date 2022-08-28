from objects.Participant import Participant
import logging
import json
import math

config = {
    "id": "CLIENT_5",
    "name": "field",
    "subscribed_topics": ["field_update"],
    "non_essential_subscribed_topics": ["field_update_realtime"],
    "published_topics": ["field"],
    "constants_required": [],
    "variables_subscribed": [],
}
init_topic_data = {
    "currentTimestep": 0,
    "currentTime": 0,
    "totalTimestepsRun": 0,
    "versions": 1,
}
CONSTANTS = {
    "timestepSize": 1,
    "totalTimesteps": 500,
    "requiredThrust": 123_191_000.0,
    "dragCoefficient": 0.75,
    "rocketTotalMass": 7_982_000,
    "rocketUnfuelledMass": 431_000,
    "initialRocketOFMass": 0,
    "O2FRatio": 6,
    "initialOxidiserMass": 0,
    "initialFuelMass": 0,
    "rocketBodyDiameter": 21.3,
    "rocketFrontalArea": 0,
    "specificImpulse": 410,
    "gravitationalAcceleration": 9.81,
    "initialRequiredMassFlowRate": 0,
}

field_participant = Participant(
    CONFIG_DATA=config,
    topic_data=init_topic_data,
    CONSTANTS=CONSTANTS,
    is_field_participant=True,
)

# Actual Analysis
def run_one_cycle_ow():

    logging.info(f"Sending topic 'field' as :{field_participant.topic_data}")

    if field_participant.all_data_dict and (
        field_participant.all_data_dict[
            [key for key in field_participant.all_data_dict.keys()][-1]
        ]["currentTimestep"]
        + 1
        != field_participant.topic_data["currentTimestep"]
    ):
        logging.debug(f"Received Updation : {field_participant.variables=}")
        field_participant.topic_data["versions"] = (
            field_participant.topic_data["versions"] + 1
        )

    field_participant.all_data_dict[
        f"{field_participant.topic_data['versions']}.{field_participant.topic_data['currentTimestep']}"
    ] = field_participant.variables.copy()
    field_participant.send_topic_data(
        field_participant.server_socket,
        "field",
        json.dumps(field_participant.variables),
    )

    if field_participant.topic_data["currentTimestep"] == 246:
        logging.info(f"\n\n\n{json.dumps(field_participant.all_data_dict, indent=4)}")


def fill_init_topic_data_ow():
    field_participant.topic_data["currentOxidiserMass"] = field_participant.CONSTANTS[
        "initialOxidiserMass"
    ]
    field_participant.topic_data["currentFuelMass"] = field_participant.CONSTANTS[
        "initialFuelMass"
    ]
    field_participant.topic_data[
        "currentRocketTotalMass"
    ] = field_participant.CONSTANTS["rocketTotalMass"]

    field_participant.data_dict["currentMassFlowRate"] = 0
    field_participant.data_dict["currentOxidiserMass"] = field_participant.CONSTANTS[
        "initialOxidiserMass"
    ]
    field_participant.data_dict["currentFuelMass"] = field_participant.CONSTANTS[
        "initialFuelMass"
    ]
    field_participant.data_dict["currentRocketTotalMass"] = field_participant.CONSTANTS[
        "rocketTotalMass"
    ]


def start_initiation_ow():
    field_participant.CONSTANTS["initialRocketOFMass"] = (
        field_participant.CONSTANTS["rocketTotalMass"]
        - field_participant.CONSTANTS["rocketUnfuelledMass"]
    )
    field_participant.CONSTANTS["initialOxidiserMass"] = (
        field_participant.CONSTANTS["O2FRatio"]
        * field_participant.CONSTANTS["initialRocketOFMass"]
        / (field_participant.CONSTANTS["O2FRatio"] + 1)
    )
    field_participant.CONSTANTS["initialFuelMass"] = field_participant.CONSTANTS[
        "initialRocketOFMass"
    ] / (field_participant.CONSTANTS["O2FRatio"] + 1)
    field_participant.CONSTANTS["rocketFrontalArea"] = (
        math.pi
        * field_participant.CONSTANTS["rocketBodyDiameter"]
        * field_participant.CONSTANTS["rocketBodyDiameter"]
    )
    field_participant.CONSTANTS[
        "initialRequiredMassFlowRate"
    ] = field_participant.CONSTANTS["requiredThrust"] / (
        field_participant.CONSTANTS["specificImpulse"]
        * field_participant.CONSTANTS["gravitationalAcceleration"]
    )


def listen_analysis_ow():
    # global received_updation
    field_participant.run_one_cycle()
    while True:
        topic, sent_time, recv_time, info = field_participant.recv_topic_data(
            field_participant.server_socket
        )
        if topic == "field_update":
            can_continue = process_topic_field_update(
                info, sent_time, recv_time, variables
            )
            if can_continue:
                field_participant.start_a_cycle()
            else:
                break
        # elif topic == "field_update_realtime":
        #     can_continue = process_topic_field_update(
        #         info, sent_time, recv_time, variables
        #     )
        #     received_updation = True

        #     if can_continue:
        #         start_a_cycle()
        #     else:
        #         break


field_participant.run_one_cycle = run_one_cycle_ow
field_participant.fill_init_topic_data = fill_init_topic_data_ow
field_participant.start_initiation = start_initiation_ow
field_participant.main()
