from pydantic import BaseModel

from aipolabs.common.logging import get_logger
from aipolabs.server.apps.base import AppBase

logger = get_logger(__name__)


class Person(BaseModel):
    name: str
    title: str


class Location(BaseModel):
    city: str
    country: str


# TODO: how should we handle args are passed as flattened? separated by double underscore?
# e.g. person__name, person__title. maybe need to preprocess the args before passing to the method?
class AipolabsTest(AppBase):
    """
    Aipolabs Test App that corresponds to the aipolabs_test.json file in the tests/dummy_apps directory.
    """

    def hello_world(self, name: str, greeting: str) -> dict:
        logger.info(
            "executing hello_world",
            extra={"name": name, "greeting": greeting},
        )
        return {"message": f"{greeting}, {name}!"}

    def hello_world_nested_args(self, person: Person, greeting: str, location: Location) -> dict:
        # Ensure 'person' is a Person instance
        if isinstance(person, dict):
            person = Person(**person)
        if isinstance(location, dict):
            location = Location(**location)
        logger.info(
            "executing hello_world_nested_args",
            extra={
                "person": person,
                "greeting": greeting,
                "location": location,
            },
        )
        return {
            "message": f"{greeting}, {person.title} {person.name} in {location.city}, {location.country}!"
        }

    def hello_world_no_args(self) -> dict:
        logger.info("executing hello_world_no_args")
        return {"message": "Hello, world!"}
