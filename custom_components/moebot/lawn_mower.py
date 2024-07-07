import logging
from builtins import super

import graphviz
import networkx as nx
import pydot
from homeassistant.components.lawn_mower import LawnMowerEntity, LawnMowerEntityEntityDescription, \
    LawnMowerEntityFeature, LawnMowerActivity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pymoebot import MoeBot
from transitions.extensions import GraphMachine

from custom_components.moebot import BaseMoeBotEntity
from .const import DOMAIN

_STATUS_TO_HA = {
    "STANDBY": LawnMowerActivity.DOCKED,
    "MOWING": LawnMowerActivity.MOWING,
    "CHARGING": LawnMowerActivity.DOCKED,
    "EMERGENCY": LawnMowerActivity.ERROR,
    "LOCKED": LawnMowerActivity.ERROR,
    "PAUSED": LawnMowerActivity.PAUSED,
    "PARK": LawnMowerActivity.MOWING,
    "CHARGING_WITH_TASK_SUSPEND": LawnMowerActivity.DOCKED,
    "FIXED_MOWING": LawnMowerActivity.MOWING,
    "ERROR": LawnMowerActivity.ERROR,
}

_log = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant,
                            entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    """Set up MoeBot from a config entry."""
    moebot = hass.data[DOMAIN][entry.entry_id]

    moebot_entity = MoeBotMowerEntity(moebot)
    async_add_entities([moebot_entity])


class MoeBotStateMachine(GraphMachine):
    states = ['STANDBY', 'MOWING', 'FIXED_MOWING', 'PAUSED', 'PARK', 'CHARGING', 'CHARGING_WITH_TASK_SUSPEND', 'LOCKED',
              'EMERGENCY', 'ERROR']

    def __init__(self, moebot: MoeBot):
        super().__init__(self, states=self.states, use_pygraphviz=False,
                         initial="STANDBY", auto_transitions=False)
        _log.info(f"Graphviz: {graphviz.__version__}")
        _log.info(f"PyDot: {pydot.__version__}")

        self._moebot: MoeBot = moebot

        # This call back ensures that the state of the state machine is kept in sync with the state of the
        # MoeBot.
        def __state_listener(raw_msg):
            _log.debug("%r got an update: %r" % (self.__class__.__name__, raw_msg))
            self.state = self._moebot.state

        self._moebot.add_listener(__state_listener)
        self.add_transition('StartMowing', 'CHARGING', 'MOWING',
                            before=self._moebot.start)
        self.add_transition('StartMowing', 'STANDBY', 'MOWING',
                            before=self._moebot.start)
        self.add_transition('PauseWork', 'MOWING', 'PAUSED',
                            before=self._moebot.pause)
        self.add_transition('ContinueWork', 'PAUSED', 'MOWING',
                            before=self._moebot.start)
        self.add_transition('CancelWork', 'PAUSED', 'STANDBY',
                            before=self._moebot.cancel)
        self.add_transition('StartReturnStation', 'STANDBY', 'PARK',
                            before=self._moebot.dock)
        self.add_transition('Error', '*', 'ERROR')
        self.add_transition('Emergency', '*', 'EMERGENCY')
        self.add_transition('Locked', '*', 'LOCKED')

    def shortest_path(self, target):
        # With thanks for support from @aleneum per https://github.com/pytransitions/transitions/discussions/679
        graph = nx.drawing.nx_pydot.from_pydot(
            pydot.graph_from_dot_data(self.get_graph().source)[0]
        )
        path = nx.shortest_path(graph, self.state, target)
        # the pydot graph seems to be slightly different organized and returns a list of edges.
        for trigger in (
                graph[u][v][0].get("label") for u, v in nx.utils.pairwise(path)
        ):
            _log.debug(f"Executing {trigger}...")
            self.trigger(trigger)


class MoeBotMowerEntity(BaseMoeBotEntity, LawnMowerEntity):
    entity_description: LawnMowerEntityEntityDescription
    _attr_supported_features = (
            LawnMowerEntityFeature.DOCK
            | LawnMowerEntityFeature.PAUSE
            | LawnMowerEntityFeature.START_MOWING
    )

    def __init__(self, moebot: MoeBot):
        super().__init__(moebot)

        # A unique_id for this entity within this domain.
        # Note: This is NOT used to generate the user visible Entity ID used in automations.
        self._attr_unique_id = f"{self._moebot.id}_mower"

        self._attr_name = f"MoeBot Mower"

        self.__attr_icon = "mdi:robot-mower"
        # The Lawn Mower Entity is actually the Device for the MoeBot integration. Therefore, we can provide the
        # other supporting metadata about the Device.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._moebot.id)},
            manufacturer="MoeBot",
            name=f"{self.name} ({self._moebot.id})",
        )

        self._sm: MoeBotStateMachine = MoeBotStateMachine(self._moebot)

    @property
    def activity(self) -> LawnMowerActivity | None:
        """Return the state of the mower."""
        mb_state = self._moebot.state
        return _STATUS_TO_HA[mb_state]

    def start_mowing(self) -> None:
        self._sm.shortest_path('MOWING')

    def dock(self) -> None:
        self._sm.shortest_path('PARK')

    def pause(self) -> None:
        self._sm.shortest_path('PAUSED')
