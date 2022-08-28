from objects.Participant import Participant
import logging
import json

config = {
    "id": "CLIENT_3",
    "name": "motion",
    "subscribed_topics": ["drag", "thrust", "fuel_flow", "field"],
    "non_essential_subscribed_topics": ["motion_update_realtime"],
    "published_topics": ["motion"],
    "constants_required": [
        "gravitationalAcceleration",
        "requiredThrust",
        "timestepSize",
        "totalTimesteps",
    ],
    "variables_subscribed": [],
}
init_topic_data = {
    "netThrust": 0,
    "currentAcceleration": 0,
    "currentVelocityDelta": 0,
    "currentVelocity": 0,
    "currentAltitudeDelta": 0,
    "currentAltitude": 0,
    "requiredThrustChange": 0,
}

motion_participant = Participant(CONFIG_DATA=config, topic_data=init_topic_data)

# Actual Analysis
def run_one_cycle_ow():
    motion_participant.topic_data["netThrust"] = (
        motion_participant.CONSTANTS["requiredThrust"]
        - motion_participant.data_dict["currentRocketTotalMass"]
        * motion_participant.CONSTANTS["gravitationalAcceleration"]
        - motion_participant.data_dict["drag"]
    )
    motion_participant.topic_data["requiredThrustChange"] = (
        (
            motion_participant.CONSTANTS["requiredThrust"]
            - motion_participant.topic_data["netThrust"]
        )
        * 100
        / motion_participant.CONSTANTS["requiredThrust"]
    )
    motion_participant.topic_data["currentAcceleration"] = (
        motion_participant.topic_data["netThrust"]
        / motion_participant.data_dict["currentRocketTotalMass"]
    )
    motion_participant.topic_data["currentVelocityDelta"] = (
        motion_participant.topic_data["currentAcceleration"]
        * motion_participant.CONSTANTS["timestepSize"]
    )
    motion_participant.topic_data["currentVelocity"] = (
        motion_participant.topic_data["currentVelocity"]
        + motion_participant.topic_data["currentVelocityDelta"]
    )
    motion_participant.topic_data["currentAltitudeDelta"] = (
        motion_participant.topic_data["currentVelocity"]
        * motion_participant.CONSTANTS["timestepSize"]
    )
    motion_participant.topic_data["currentAltitude"] = (
        motion_participant.topic_data["currentAltitude"]
        + motion_participant.topic_data["currentAltitudeDelta"]
    )
    # if motion_participant.data_dict["currentTimestep"] in [60, 105, 185]:
    #     print(f'Reduced at {motion_participant.data_dict["currentTimestep"]=}')
    #     motion_participant.topic_data["currentAltitude"] -= 250

    motion_participant.all_data_dict[
        f"{motion_participant.data_dict['versions']}.{motion_participant.data_dict['currentTimestep']}"
    ] = motion_participant.topic_data.copy()

    motion_participant.send_topic_data(
        motion_participant.server_socket,
        "motion",
        json.dumps(motion_participant.topic_data),
    )
    logging.info(f"Received {motion_participant.data_dict=}")
    logging.info(
        f"Timestep: {motion_participant.data_dict['currentTimestep']:5}-{motion_participant.topic_data}"
    )
    if motion_participant.data_dict["currentTimestep"] == 245:
        logging.info(f"\n\n\n{json.dumps(motion_participant.all_data_dict, indent=4)}")


def fill_init_topic_data_ow():
    motion_participant.topic_data["currentAcceleration"] = 0
    motion_participant.topic_data["currentVelocity"] = 0
    motion_participant.topic_data["currentAltitude"] = 0


motion_participant.run_one_cycle = run_one_cycle_ow
motion_participant.fill_init_topic_data = fill_init_topic_data_ow
motion_participant.main()
