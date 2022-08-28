from objects.Participant import Participant
import logging
import json

config = {
    "id": "CLIENT_1",
    "name": "fuel_flow",
    "subscribed_topics": ["thrust", "field"],
    "non_essential_subscribed_topics": ["fuel_flow_update_realtime"],
    "published_topics": ["fuel_flow"],
    "constants_required": [
        "specificImpulse",
        "gravitationalAcceleration",
        "O2FRatio",
        "initialOxidiserMass",
        "initialFuelMass",
        "rocketTotalMass",
        "timestepSize",
        "totalTimesteps",
    ],
    "variables_subscribed": [],
}
init_topic_data = {
    "currentMassFlowRate": 0,
    "currentOxidiserMass": 0,
    "currentFuelMass": 0,
    "currentRocketTotalMass": 0,
}

fuel_participant = Participant(CONFIG_DATA=config, topic_data=init_topic_data)

# Actual Analysis
def run_one_cycle_ow():
    fuel_participant.data_dict["currentMassFlowRate"] = fuel_participant.data_dict[
        "currentThrust"
    ] / (
        fuel_participant.CONSTANTS["specificImpulse"]
        * fuel_participant.CONSTANTS["gravitationalAcceleration"]
    )
    fuel_participant.fuel_participant.topic_data[
        "currentMassFlowRate"
    ] = fuel_participant.data_dict["currentMassFlowRate"]

    massReduced = (
        fuel_participant.data_dict["currentMassFlowRate"]
        * fuel_participant.CONSTANTS["timestepSize"]
    )
    fuel_participant.data_dict["currentOxidiserMass"] = fuel_participant.data_dict[
        "currentOxidiserMass"
    ] - (
        massReduced
        * fuel_participant.CONSTANTS["O2FRatio"]
        / (fuel_participant.CONSTANTS["O2FRatio"] + 1)
    )
    fuel_participant.topic_data["currentOxidiserMass"] = fuel_participant.data_dict[
        "currentOxidiserMass"
    ]
    fuel_participant.data_dict["currentFuelMass"] = fuel_participant.data_dict[
        "currentFuelMass"
    ] - (massReduced / (fuel_participant.CONSTANTS["O2FRatio"] + 1))
    fuel_participant.topic_data["currentFuelMass"] = fuel_participant.data_dict[
        "currentFuelMass"
    ]
    # TODO: if fuel empty, send "STOP" of timestep = -1 to field, thus stopping analysis
    if fuel_participant.topic_data["currentFuelMass"] <= 0:
        fuel_participant.send_topic_data(
            "field_update",
            json.dumps({"currentTimestep": -1}),
        )
    fuel_participant.data_dict["currentRocketTotalMass"] = (
        fuel_participant.data_dict["currentRocketTotalMass"] - massReduced
    )
    fuel_participant.topic_data["currentRocketTotalMass"] = fuel_participant.data_dict[
        "currentRocketTotalMass"
    ]
    logging.info(f"Received {fuel_participant.data_dict=}")
    logging.info(
        f"Timestep: {fuel_participant.data_dict['currentTimestep']:5}-{fuel_participant.topic_data}"
    )
    fuel_participant.send_topic_data(
        "fuel_flow",
        json.dumps(fuel_participant.topic_data),
    )


def fill_init_topic_data_ow():
    fuel_participant.topic_data["currentOxidiserMass"] = fuel_participant.CONSTANTS[
        "initialOxidiserMass"
    ]
    fuel_participant.topic_data["currentFuelMass"] = fuel_participant.CONSTANTS[
        "initialFuelMass"
    ]
    fuel_participant.topic_data["currentRocketTotalMass"] = fuel_participant.CONSTANTS[
        "rocketTotalMass"
    ]

    fuel_participant.data_dict["currentMassFlowRate"] = 0
    fuel_participant.data_dict["currentOxidiserMass"] = fuel_participant.CONSTANTS[
        "initialOxidiserMass"
    ]
    fuel_participant.data_dict["currentFuelMass"] = fuel_participant.CONSTANTS[
        "initialFuelMass"
    ]
    fuel_participant.data_dict["currentRocketTotalMass"] = fuel_participant.CONSTANTS[
        "rocketTotalMass"
    ]


fuel_participant.run_one_cycle = run_one_cycle_ow
fuel_participant.fill_init_topic_data = fill_init_topic_data_ow
fuel_participant.main()
