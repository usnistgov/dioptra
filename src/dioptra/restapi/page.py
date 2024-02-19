# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode


class Page:
    """Page object.

    Attributes:
        data: List of data matching page parameters.
        index: Start of page.
        is_complete: Boolean indicating if more data is available.
        first: URL to first page in result set.
        next: URL to next page in result set.
        last: URL to last page in result set.
    """

    def __init__(
        self, data: list, index: int, is_complete: bool, endpoint: str, page_length: int
    ):
        self.data = data
        self.index = index
        self.is_complete = is_complete
        self.first = self.pageUrl(endpoint, 0, page_length)
        self.next = self.pageUrl(endpoint, index + page_length, page_length)
        self.prev = self.pageUrl(endpoint, index - page_length, page_length)

    def pageUrl(self, endpoint: str, index: int, page_length: int) -> str:
        """
        Return a url for a given page.

        Args:
            endpoint: endpoint url for generating pages.
            index: Index of page.
            page_length: Length of page.
        """
        if index < 0:
            index = 0
        url = f"/api/{endpoint}?index={index}&pageLength={page_length}"
        return url
