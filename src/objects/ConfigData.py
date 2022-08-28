from typing import List


class ConfigData:
    def __init__(
        self,
        config_json: dict = {},
        id: str = "",
        name: str = "",
        subscribed_topics: List[str] = [],
        non_essential_subscribed_topics: List[str] = [],
        published_topics: List[str] = [],
        constants_required: List[str] = [],
        variables_subscribed: List[str] = [],
    ) -> None:
        if config_json:
            self.id = config_json["id"]
            self.name = config_json["name"]
            self.subscribed_topics = config_json["subscribed_topics"]
            self.non_essential_subscribed_topics = (
                config_json["non_essential_subscribed_topics"]
                if "non_essential_subscribed_topics" in config_json.keys()
                else []
            )
            self.published_topics = config_json["published_topics"]
            self.constants_required = config_json["constants_required"]
            self.variables_subscribed = config_json["variables_subscribed"]
        else:
            self.id = id
            self.name = name
            self.subscribed_topics = subscribed_topics
            self.non_essential_subscribed_topics = non_essential_subscribed_topics
            self.published_topics = published_topics
            self.constants_required = constants_required
            self.variables_subscribed = variables_subscribed
