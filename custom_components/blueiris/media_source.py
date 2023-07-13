"""Expose cameras as media sources."""
from __future__ import annotations
import logging

from homeassistant.components.media_player import BrowseError, MediaClass
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)
from homeassistant.core import HomeAssistant

from . import get_ha
from .helpers.const import *

_LOGGER = logging.getLogger(__name__)


async def async_get_media_source(hass: HomeAssistant) -> BlueIrisMediaSource:
    """Set up Blue Iris media source."""
    return BlueIrisMediaSource(hass)


class BlueIrisMediaSource(MediaSource):
    """Provide camera feeds as media sources."""

    name: str = "Blue Iris"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize CameraMediaSource."""
        super().__init__(DOMAIN)
        self.hass = hass

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a url."""
        entity_id = self.hass.data[DATA_BLUEIRIS][DATA_BLUEIRIS_HA_ENTITIES][0]
        ha = get_ha(self.hass, entity_id)
        url = ha.api.get_clip_stream_url(item.identifier, 10345040)
        _LOGGER.info(f"Resolving media url: {url}")

        return PlayMedia(url, "image/jpeg")

    async def async_browse_media(
            self,
            item: MediaSourceItem,
    ) -> BrowseMediaSource:
        """Return media."""
        if item.identifier:
            raise BrowseError("Unknown item")

        can_stream_hls = "stream" in self.hass.config.components

        # Root. List cameras.
        children = []
        for entity_id in self.hass.data[DATA_BLUEIRIS][DATA_BLUEIRIS_HA_ENTITIES]:
            ha = get_ha(self.hass, entity_id)
            not_shown = 0
            alerts = await ha.api.list_alerts()
            for alert in alerts:
                if True:
                    content_type = ""
                else:
                    not_shown += 1
                    continue

                children.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=alert.clip,
                        media_class=MediaClass.VIDEO,
                        media_content_type=content_type,
                        title=f"{alert.camera} {alert.date} {alert.memo}",
                        thumbnail=f"{ha.api.base_url}/thumbs/{alert.path}",
                        can_play=True,
                        can_expand=False,
                    )
                )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.APP,
            media_content_type="",
            title="Blue Iris",
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.VIDEO,
            children=children,
            not_shown=not_shown,
        )
