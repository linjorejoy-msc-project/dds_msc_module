import objects.DDSDomain as DDSDomain
import logging

FORMAT = "%(levelname)-10s %(asctime)s: %(message)s"
logging.basicConfig(
    handlers=[
        logging.FileHandler(filename="src/LOGS/logs.log", encoding="utf-8", mode="w")
    ],
    level=logging.DEBUG,
    format=FORMAT,
)

topics = [
    {
        "name": "fuel_flow",
        "type": "receive",
        "regex": "",
        "parameters_present": [
            "currentMassFlowRate",
            "currentOxidiserMass",
            "currentFuelMass",
            "currentRocketTotalMass",
        ],
    },
    {
        "name": "thrust",
        "type": "receive",
        "regex": "",
        "parameters_present": [
            "currentThrust",
        ],
    },
    {
        "name": "drag",
        "type": "receive",
        "regex": "",
        "parameters_present": [
            "drag",
        ],
    },
    {
        "name": "motion",
        "type": "receive",
        "regex": "",
        "parameters_present": [
            "netThrust",
            "currentAcceleration",
            "currentVelocityDelta",
            "currentVelocity",
            "currentAltitudeDelta",
            "currentAltitude",
            "requiredThrustChange",
        ],
    },
    {
        "name": "field",
        "type": "receive",
        "regex": "",
        "parameters_present": [
            "currentTimestep",
            "currentTime",
            "totalTimestepsRun",
            "versions",
        ],
    },
    {
        "name": "atmosphere",
        "type": "receive",
        "regex": "",
        "parameters_present": [
            "pressure",
            "temperature",
            "density",
        ],
    },
    {"name": "field_update", "type": "receive", "regex": "", "parameters_present": []},
    {
        "name": "field_update_realtime",
        "type": "update",
        "regex": "",
        "parameters_present": [],
    },
    {
        "name": "motion_update_realtime",
        "type": "update",
        "regex": "",
        "parameters_present": [],
    },
    {
        "name": "fuel_flow_update_realtime",
        "type": "update",
        "regex": "",
        "parameters_present": [],
    },
]

dds_obj = DDSDomain.DDSDomain(topics=topics)
dds_obj.main()
