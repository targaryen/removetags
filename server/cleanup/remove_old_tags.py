from aqcommon.logger import FCLogger
import os
import requests
from aqcommon.resthelper import combined_api_get_result
import json
from dateutil.parser import parse
import operator
import datetime
import re
import time

# Initialization
try:
    DATA_DIR = os.environ.get("DATA_DIR").strip()
except:
    DATA_DIR = "/usr/app/out/trdata"
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        os.chmod(DATA_DIR, 0o755)
DEBUG_LEVEL = os.environ.get("DEBUG_LEVEL")
if DEBUG_LEVEL is None:
    DEBUG_LEVEL = "INFO"

logger = FCLogger(DATA_DIR + '/debug.log', DEBUG_LEVEL, "tag_remover")
# logger = ConsoleLogger('DEBUG', "tag_remover")

AQUA_URL = os.environ.get("AQUA_URL")
AQUA_USER = os.environ.get("AQUA_USER")
AQUA_PASSWORD = os.environ.get("AQUA_PASSWORD")
NUMBER_KEEP_TAGS = os.environ.get("NUMBER_KEEP_TAGS")

bad_env = False
if AQUA_URL is None:
    bad_env = True
    logger.critical("You must set AQUA_URL environment variable.")
if AQUA_USER is None:
    bad_env = True
    logger.critical("You must set AQUA_USER environment variable.")
if AQUA_PASSWORD is None:
    bad_env = True
    logger.critical("You must set AQUA_PASSWORD environment variable.")
if NUMBER_KEEP_TAGS is None:
    bad_env = True
    logger.critical("You must set NUMBER_KEEP_TAGS environment variable.")

AQUA_URL = AQUA_URL.rstrip("/")
NUMBER_KEEP_TAGS = int(NUMBER_KEEP_TAGS)

if bad_env:
    logger.critical("Exiting due to missing environment variables.")
    exit(1)

if os.environ.get("IGNORE_TAGS") is not None:
    IGNORE_TAGS = os.environ.get("IGNORE_TAGS").split(",")
else:
    IGNORE_TAGS = []

auth = requests.auth.HTTPBasicAuth(username=AQUA_USER, password=AQUA_PASSWORD)


def retrieve_image_list():
    """
    Retrieves list of images
    :return: List containing registry name and repo/image:tags 
    """
    logger.debug("Retrieving list of images")

    repo_list_append = "/api/v1/repositories?filter=&order_by=name+asc"
    repo_url = AQUA_URL + repo_list_append
    images = combined_api_get_result(repo_url, auth, timeout=600, pagesize=7)
    unique_registries = list()
    registries = dict()
    for image in images:
        if image['registry'] not in unique_registries:
            unique_registries.append(image['registry'])
            registries[image['registry']] = list()
        registries[image['registry']].append(image['name'])
    logger.debug(registries)
    return registries


def sanitize_filename(unclean_filename):
    clean_filename = str(unclean_filename).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', clean_filename)


def export_tag(registry, repository, tag, uuid):
    # /api/v1/images/export
    export_data = dict()
    image_data = {
        "registry": registry,
        "repository": repository,
        "tag": tag,
        "uid": uuid,
        "digest": None,
        "source": None
    }
    export_data['images'] = list()
    export_data['images'].append(image_data)
    export_url = AQUA_URL + "/api/v1/images/export"
    logger.debug("Export data: %s" % (json.dumps(export_data),))
    response = requests.post(export_url, auth=auth, timeout=600, data=json.dumps(export_data))
    if response.status_code == 200:
        if len(response.json()['images']) == 0:
            logger.debug("No data to export for image.")
            return True
        logger.debug("Response: " + str(response.status_code))
        logger.debug("Response: " + str(response.text))
        export_dir = DATA_DIR + "/export"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        export_filename = registry + "." \
                          + repository.replace("/", "-") + "." \
                          + tag + "." \
                          + str(int(time.mktime(datetime.datetime.now().timetuple()))) \
                          + ".json"
        export_filename = export_dir + "/" + sanitize_filename(export_filename)
        with open(export_filename, 'w') as outfile:
            outfile.write(response.text)
        return True
    else:
        logger.error("Failed delete.  Response code: %s" % (str(response.status_code)))
        return False


def delete_tag(registry, repository, tag, uuid):
    logger.info("Deleting '%s:%s' on registry '%s'." % (repository, tag, registry))
    delete_data = dict()
    image_data = {
        "registry": registry,
        "repository": repository,
        "tag": tag,
        "uid": uuid,
        "digest": None,
        "source": None
    }
    delete_data['images'] = list()
    delete_data['images'].append(image_data)
    logger.debug("Delete data: %s" % (json.dumps(delete_data),))
    delete_url = AQUA_URL + "/api/v1/images/delete"
    response = requests.post(delete_url, auth=auth, timeout=600, data=json.dumps(delete_data))
    if response.status_code == 204:
        logger.debug("Response: " + str(response.status_code))
        return True
    else:
        logger.error("Failed delete.  Response code: %s" % (str(response.status_code)))
        return False


def prune_tags(registry, image, tags):
    counted_tags = list()
    create_times = list()
    update_times = list()
    for tagdata in tags:
        tag = dict()
        metadata = json.loads(tagdata['metadata'])
        if tagdata['tag'] not in IGNORE_TAGS:
            tag['registry'] = registry
            tag['image'] = image
            tag['repo'] = tagdata['reponame']
            tag['uuid'] = tagdata['uid']
            tag['create_time'] = tagdata['create_time']
            tag['lastupdate'] = tagdata['lastupdate']
            tag['metadata_create'] = parse(metadata['created']).timestamp()
            tag['tag'] = tagdata['tag']
            counted_tags.append(tag)
            if tag['create_time'] not in create_times:
                create_times.append(tag['create_time'])
            if tag['lastupdate'] not in update_times:
                update_times.append(tag['lastupdate'])
        logger.debug(tag)

    # Sort the tags by create_time
    counted_tags.sort(key=operator.itemgetter('metadata_create'), reverse=True)
    logger.debug("SORTED list of tags found:")
    for tag in counted_tags:
        logger.debug("SORTED: %s, (m)create: %s, lastupdate: %s, create_time: %s"
                     % (tag['image'],
                        str(tag['metadata_create']),
                        str(tag['lastupdate']),
                        str(tag['create_time'])))

    if len(counted_tags) > NUMBER_KEEP_TAGS:
        tags_to_remove = counted_tags[NUMBER_KEEP_TAGS:]
        tags_to_remove.reverse()

        logger.info("Removing %s tags" % (str(len(tags_to_remove)),))

        for tag in tags_to_remove:

            export_result = export_tag(tag['registry'], tag['repo'], tag['tag'], tag['uuid'])
            if export_result:
                delete_tag(tag['registry'], tag['repo'], tag['tag'], tag['uuid'])
                pass
            else:
                logger.error("Could not export image data, therefore will not delete image.")

    return None


def retrieve_tag_list(registry, image):
    # /api/v1/images/artif/library/clawless
    tag_url = AQUA_URL + "/api/v1/images/" + registry + "/" + image
    response = requests.get(tag_url, auth=auth, timeout=900).json()
    if response['images_count'] > NUMBER_KEEP_TAGS:
        logger.info("Pruning tags for '" + image + "' on registry '" + registry + "'")
        logger.info("Pruning '%s' on registry '%s', keeping %s of %s tags." % (image,
                                                                               registry,
                                                                               str(NUMBER_KEEP_TAGS),
                                                                               str(response['images_count'])))
        tags = response['images']
        prune_tags(registry, image, tags)
    else:
        logger.debug("No need to prune tags for '" + image + "' on registry '" + registry + "'")
    return None


if __name__ == '__main__':
    logger.info("Aqua image tag cleanup script, v1.0")
    logger.info("Using Aqua console as %s on %s" % (AQUA_USER, AQUA_URL))
    logger.info("Keeping most recently added %s tags." % (str(NUMBER_KEEP_TAGS),))
    repos = retrieve_image_list()
    try:
        for registry in repos.keys():
            for image in repos[registry]:
                if '/' not in image:
                    image = 'library/' + str(image)
                logger.debug("Processing '" + str(image) + "' on registry '" + str(registry) + "'.")
                all_tags = retrieve_tag_list(registry, image)
    except KeyboardInterrupt:
        logger.warn("User canceled session (CTRL-C)")
