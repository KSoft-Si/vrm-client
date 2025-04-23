from datetime import datetime
from typing import Optional, Any

from ._base import BaseClientModule
from .. import consts
from ..models import User, Site, AccessToken


class UsersModule(BaseClientModule):
    BASE_URL = consts.USERS_URL

    async def get_me(self):
        """Get the current user."""
        request = await self._client._request(
            method="GET",
            url=consts.USER_ME_URL,
        )
        return User(**request["user"])

    async def add_site(self, installation_identifier: str) -> dict[str, str]:
        """
        Adds a new site based on the given installation identifier.

        :param installation_identifier: A string representing the unique identifier
            for the site installation.
        :return: A dictionary containing the site_id and site_name.
        """
        request = await self._client._request(
            method="POST",
            url=f"{self.BASE_URL}/{await self._client._get_user_id()}/addSite",
            json_data={
                "installation_identifier": installation_identifier,
            },
        )
        return request["records"]

    async def list_sites(
        self,
        extended: bool = False,
        site_id: int | None = None,
    ) -> list[Site]:
        """
        Lists all sites associated with the user.

        :return: A SiteList object containing the list of sites.
        """
        query_params = {}
        if extended:
            query_params["extended"] = 1
        if site_id:
            query_params["idSite"] = site_id
        request = await self._client._request(
            method="GET",
            url=f"{self.BASE_URL}/{await self._client._get_user_id()}/installations",
            params=query_params,
        )
        return [Site(**site) for site in request["records"]]

    async def get_site(self, site_id: int, extended: bool = False) -> Site | None:
        """
        Retrieves detailed information about a specific site.

        :param site_id: The ID of the site to retrieve.
        :return: A Site object containing detailed information about the site.
        """
        sites = await self.list_sites(extended=extended, site_id=site_id)
        if not sites:
            return None
        return sites[0]

    async def create_access_token(
        self, name: str, expiry: Optional[int | datetime] = None
    ) -> str:
        """
        Creates an access token for the user.

        :param name: The name of the access token.
        :param expiry: Optional expiry time for the token. Can be a timestamp or a datetime object.
        :return: The created access token.
        """
        if isinstance(expiry, datetime):
            expiry = int(expiry.timestamp())

        payload = {
            "name": name,
        }
        if expiry is not None:
            payload["expiry"] = expiry

        request = await self._client._request(
            method="POST",
            url=f"{self.BASE_URL}/{await self._client._get_user_id()}/accesstokens/create",
            json_data=payload,
        )
        return request["token"]

    async def list_access_tokens(self) -> list[AccessToken]:
        """
        Lists all access tokens for the user.

        :return: A list of dictionaries containing access token information.
        """
        request = await self._client._request(
            method="GET",
            url=f"{self.BASE_URL}/{await self._client._get_user_id()}/accesstokens/list",
        )
        return request["tokens"]

    async def revoke_access_token(self, token_id: int | AccessToken) -> bool:
        """
        Revokes an access token.

        :param token_id: The ID of the access token to revoke.
        """
        if isinstance(token_id, AccessToken):
            token_id = token_id.id

        response = await self._client._request(
            method="GET",
            url=f"{self.BASE_URL}/{await self._client._get_user_id()}/accesstokens/{token_id}/revoke",
        )
        return response["data"]["removed"] > 0

    async def get_site_id_from_identifier(
        self, installation_identifier: str
    ) -> Optional[int]:
        """
        Retrieves the site ID based on the installation identifier.

        :param installation_identifier: The unique identifier for the site installation.
        :return: The site ID if found, otherwise None.
        """
        response = await self._client._request(
            method="POST",
            url=f"{self.BASE_URL}/{await self._client._get_user_id()}/get-site-id",
            json_data={
                "installation_identifier": installation_identifier,
            },
            skip_success_check=True,
        )
        if not response["success"]:
            return None
        return response["records"]["site_id"]

    async def search(self, query: str) -> list[dict[str, Any]]:
        """
        Searches for users based on the provided query.

        :param query: The search query string.
        :return: A list of dictionaries containing user information.
        """
        request = await self._client._request(
            method="GET",
            url=f"{self.BASE_URL}/{await self._client._get_user_id()}/search",
            params={"query": query},
        )
        return request["results"]
