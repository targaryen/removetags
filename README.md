

# removetags:2.1.5

The script will connect to specified Aqua console and retrieve all of the images.  If the image has more than `NUMBER_KEEP_TAGS` number of tags,
it will perform a sort on `create_time` field in the image tag data.

In cases where there is more than one tag with the same `create_time` field (eg, added simultaneously
such as through 'Automatically pull images' setting in repository, or maybe 'Add all' selection in
UI tag search), it will sort according to the tag's metadata field `created`, which is from date image is created.

Based on the number of images to keep, a sublist of images to delete will be
generated.  The script will then export the image data, and store it in a timestamped
JSON file (except if it has not been scanned, then there is no output to save).

Then it will delete the image.


## Usage

docker-run

```
docker run --rm -it \
  -e AQUA_URL=http://aqua-console \
  -e AQUA_USER=adminuser \
  -e AQUA_PASSWORD=adminuserpassword \
  -e NUMBER_KEEP_TAGS=14 \
  -e DEBUG_LEVEL=INFO \
  -v /tmp:/usr/app/out:rw \
  targaryen/removetags:2.1.5
```


With the above example of /tmp being mounted, the log file will be
located at `/tmp/trdata/debug.log` and the exported images will be in
the `/tmp/trdata/export` directory.


### Required environment variables


| variable name    | value                                          |
|------------------|------------------------------------------------|
| AQUA_USER        | User with administrator role in Aqua           |
| AQUA_PASS        | Password for user in AQUA_USER                 |
| AQUA_URL         | Webaddress of aqua console (include http://xx) |
| NUMBER_KEEP_TAGS | Number of tags to keep                         |


### Optional environment variables

| variable name | value                                                                                                       |
|---------------|-------------------------------------------------------------------------------------------------------------|
| DEBUG_LEVEL   | Verbosity of logging (defaults to INFO)                                                                     |
| DATA_DIR      | Override default directory for log and exports  (inside container.  For host side, just change mount point) |



