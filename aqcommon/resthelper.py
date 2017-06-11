import logging
import math
logger = logging.getLogger(__name__)
import requests


def check_pagination(response):
    if 'count' in response.keys() and 'page' in response.keys() and 'pagesize' in response.keys():
        logger.debug("Response contains 'count', 'page', and 'pagesize' keys")
    else:
        logger.warning("Not a paginated API response.")
        return None

    if response['pagesize'] <= response['count']:
        logger.debug("Response spans multiple pages")
        return False

    return True


def combined_api_get_result(api_url, auth, timeout=600, pagesize=20):
    page = 1
    paged_url = api_url + "&page=" + str(page) + "&pagesize=" + str(pagesize)
    resp = requests.get(paged_url, auth=auth, timeout=timeout).json()
    if not check_pagination(resp):
        results = list()
        logger.debug("Need to paginate results")
        total_pages = math.ceil( float(resp['count']) / int(resp['pagesize']) )
        logger.debug("Pages to traverse: %s" % (str(total_pages),))
        results = resp['result']
        # logger.debug(results)
        # logger.debug(len(results))
        while page < total_pages:
            page += 1
            paged_url = api_url + "&page=" + str(page) + "&pagesize=" + str(pagesize)
            resp = requests.get(paged_url, auth=auth, timeout=timeout).json()
            results = results + resp['result']
            # logger.debug(results)
            # logger.debug(len(results))
        # logger.debug("Combined results [" + str(len(results)) + "]:" + str(results))
        return results
    else:
        logger.debug("No need to paginate")
        return resp['result']
    return None
